import { useEffect, useMemo, useRef, useState } from 'react';
import { createApi } from './api';
import type {
	AuditRow,
	BetterPOSConfig,
	CartLine,
	CatalogItem,
	Register,
	ReportSummary,
	Session,
	TableRow,
	Transaction,
} from './types';

interface AppProps {
	config: BetterPOSConfig;
}

function toMoney(value: number | string): string {
	const n = Number(value);
	if (Number.isNaN(n)) return '0.00';
	return n.toFixed(2);
}

function pathFromLocation(basePath: string): string {
	const base = basePath.replace(/\/$/, '');
	const current = window.location.pathname;
	if (!base || current === base || current === `${base}/`) return '/pos';
	if (current.indexOf(`${base}/`) === 0) {
		const sub = current.slice(base.length);
		return sub || '/pos';
	}
	return '/pos';
}

function useAppRoute(basePath: string): [string, (route: string) => void] {
	const [route, setRoute] = useState<string>(pathFromLocation(basePath));

	useEffect(() => {
		function onPop() {
			setRoute(pathFromLocation(basePath));
		}
		window.addEventListener('popstate', onPop);
		return () => window.removeEventListener('popstate', onPop);
	}, [basePath]);

	function navigate(nextRoute: string) {
		const normalized = nextRoute.startsWith('/') ? nextRoute : `/${nextRoute}`;
		window.history.pushState({}, '', `${basePath}${normalized}`);
		setRoute(normalized);
	}

	return [route, navigate];
}

function Banner({ error }: { error: string }) {
	if (!error) return null;
	return <div className="error-box">{error}</div>;
}

function AppHeader({
	canAdmin,
	navigate,
}: {
	canAdmin: boolean;
	navigate: (route: string) => void;
}) {
	return (
		<header className="betterpos-header">
			<h1>BetterPOS</h1>
			<nav className="header-nav">
				<a
					href="#"
					onClick={(ev) => {
						ev.preventDefault();
						navigate('/pos');
					}}
				>
					Frente de Caixa
				</a>
				{canAdmin ? (
					<a
						href="#"
						onClick={(ev) => {
							ev.preventDefault();
							navigate('/admin/dashboard');
						}}
					>
						Gestao
					</a>
				) : null}
			</nav>
		</header>
	);
}

function POSScreen({ config }: { config: BetterPOSConfig }) {
	const api = useMemo(() => createApi(config), [config]);
	const [registers, setRegisters] = useState<Register[]>([]);
	const [selectedRegister, setSelectedRegister] = useState<Register | null>(null);
	const [session, setSession] = useState<Session | null>(null);
	const [catalog, setCatalog] = useState<CatalogItem[]>([]);
	const [cart, setCart] = useState<CartLine[]>([]);
	const [loading, setLoading] = useState(false);
	const [pendingEuPagoTxId, setPendingEuPagoTxId] = useState<number | null>(null);
	const [error, setError] = useState('');
	const [notice, setNotice] = useState('');
	const eupagoPollRef = useRef<number | null>(null);

	const isPaymentPending = pendingEuPagoTxId !== null;

	useEffect(() => {
		return () => {
			if (eupagoPollRef.current !== null) {
				window.clearInterval(eupagoPollRef.current);
				eupagoPollRef.current = null;
			}
		};
	}, []);

	function refreshRegisters() {
		setLoading(true);
		setError('');
		api
			.registersList()
			.then((data) => {
				const nextRegisters = data.registers || [];
				setRegisters(nextRegisters);
				if (nextRegisters.length && !selectedRegister) {
					setSelectedRegister(nextRegisters[0]);
				}
			})
			.catch((err: Error) => setError(err.message))
			.finally(() => setLoading(false));
	}

	useEffect(() => {
		refreshRegisters();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	useEffect(() => {
		if (!selectedRegister) return;
		api
			.sessionStatus(selectedRegister.id)
			.then((data) => {
				if (data.has_open_session && data.session) {
					setSession({
						id: data.session.id,
						register_id: selectedRegister.id,
						register_name: selectedRegister.name,
						status: 'open',
					});
					return api.catalog();
				}
				setSession(null);
				setCatalog([]);
				return null;
			})
			.then((catalogData) => {
				if (catalogData?.items) {
					setCatalog(catalogData.items);
				}
			})
			.catch((err: Error) => setError(err.message));
	}, [api, selectedRegister]);

	function openSession() {
		if (!selectedRegister) return;
		const amount = window.prompt('Fundo de abertura', '0.00');
		if (amount === null) return;
		setLoading(true);
		setError('');
		setNotice('');
		api
			.sessionOpen({ register_id: selectedRegister.id, opening_float: amount })
			.then((data) => {
				setSession({
					id: data.session_id,
					register_id: selectedRegister.id,
					register_name: selectedRegister.name,
					status: data.status,
				});
				return api.catalog();
			})
			.then((catalogData) => {
				setCatalog(catalogData.items || []);
			})
			.catch((err: Error) => setError(err.message))
			.finally(() => setLoading(false));
	}

	function closeSession() {
		if (!session) return;
		const counted = window.prompt('Valor contado em caixa', '0.00');
		if (counted === null) return;
		setLoading(true);
		setError('');
		setNotice('');
		api
			.sessionClose({ register_id: session.register_id, counted_cash: counted })
			.then(() => {
				setSession(null);
				setCart([]);
				setCatalog([]);
			})
			.catch((err: Error) => setError(err.message))
			.finally(() => setLoading(false));
	}

	function addToCart(item: CatalogItem) {
		setCart((old) => {
			const existing = old.find((line) => line.item_id === item.id);
			if (existing) {
				return old.map((line) =>
					line.item_id === item.id
						? {
								...line,
								qty: line.qty + 1,
							}
						: line
				);
			}
			return old.concat([
				{
					item_id: item.id,
					name: item.name,
					price: Number(item.price || 0),
					qty: 1,
				},
			]);
		});
	}

	function clearCart() {
		setCart([]);
	}

	async function createOrderTransaction(): Promise<Transaction> {
		if (!session) {
			throw new Error('Abra uma sessao primeiro');
		}
		const lines = cart.map((line) => ({ item_id: line.item_id, quantity: line.qty }));
		const idempotency = `${Date.now()}-${session.register_id}-${cart.length}`;
		const created = await api.orderCreate({
			register_id: session.register_id,
			lines,
			idempotency_key: idempotency,
		});
		return created.transaction;
	}

	async function payCash() {
		if (!session || !cart.length || isPaymentPending) return;
		setLoading(true);
		setError('');
		setNotice('');
		try {
			const transaction = await createOrderTransaction();
			await api.payCash({ transaction_id: transaction.id });
			setCart([]);
			setNotice('Pagamento em dinheiro concluido com sucesso.');
		} catch (err) {
			setError((err as Error).message);
		} finally {
			setLoading(false);
		}
	}

	async function payEupago() {
		if (!session || !cart.length || isPaymentPending) return;
		const phoneInput = window.prompt('Numero MBWay (ex: 9XXXXXXXX)', '');
		if (phoneInput === null) return;
		const phone = phoneInput.replace(/\s+/g, '');
		if (!phone) {
			setError('Numero MBWay e obrigatorio.');
			return;
		}

		setLoading(true);
		setError('');
		setNotice('');
		try {
			const transaction = await createOrderTransaction();
			const initiated = await api.payEupago({
				transaction_id: transaction.id,
				provider: 'eupago_mbway',
				phone,
			});
			setPendingEuPagoTxId(transaction.id);

			setNotice(`EuPago iniciado (pagamento #${initiated.payment_id}). Aguarde confirmacao para continuar.`);

			if (eupagoPollRef.current !== null) {
				window.clearInterval(eupagoPollRef.current);
			}

			eupagoPollRef.current = window.setInterval(async () => {
				try {
					const status = await api.transactionStatus(transaction.id);
					if (status.transaction.state === 'paid') {
						if (eupagoPollRef.current !== null) {
							window.clearInterval(eupagoPollRef.current);
							eupagoPollRef.current = null;
						}
						setPendingEuPagoTxId(null);
						setCart([]);
						setNotice('Pagamento EuPago confirmado e marcado como pago.');
					} else if (['failed', 'expired', 'cancelled_unpaid', 'refund_partial', 'refund_full'].includes(status.transaction.state)) {
						if (eupagoPollRef.current !== null) {
							window.clearInterval(eupagoPollRef.current);
							eupagoPollRef.current = null;
						}
						setPendingEuPagoTxId(null);
						setError(`Pagamento EuPago terminou com estado: ${status.transaction.state}.`);
					}
				} catch (pollErr) {
					if (eupagoPollRef.current !== null) {
						window.clearInterval(eupagoPollRef.current);
						eupagoPollRef.current = null;
					}
					setPendingEuPagoTxId(null);
					setError((pollErr as Error).message);
				}
			}, 2500);
		} catch (err) {
			setError((err as Error).message);
		} finally {
			setLoading(false);
		}
	}

	const total = useMemo(
		() => cart.reduce((acc, line) => acc + line.price * line.qty, 0),
		[cart]
	);

	return (
		<div className="view pos-view">
			<Banner error={error} />
			{notice ? <div className="alert alert-success">{notice}</div> : null}

			<div className="pos-header">
				<div className="pos-session-info">
					<strong>Caixa: </strong>
					{selectedRegister ? selectedRegister.name : 'Nenhuma selecionada'} {loading ? '(a carregar...)' : ''}
					{isPaymentPending ? ' (pagamento pendente)' : ''}
				</div>
				<div className="pos-controls">
					<select
						className="register-select"
						value={selectedRegister ? selectedRegister.id : ''}
						disabled={isPaymentPending}
						onChange={(ev) => {
							const id = Number(ev.target.value);
							const reg = registers.find((r) => r.id === id);
							setSelectedRegister(reg || null);
						}}
					>
						<option value="">Selecionar caixa</option>
						{registers.map((reg) => (
							<option key={reg.id} value={reg.id}>
								{reg.name} ({reg.code})
							</option>
						))}
					</select>{' '}
					{session ? (
						<button className="session-btn session-btn-close" onClick={closeSession} disabled={loading || isPaymentPending}>
							Fechar sessao
						</button>
					) : (
						<button className="session-btn session-btn-open" onClick={openSession} disabled={!selectedRegister || loading || isPaymentPending}>
							Abrir sessao
						</button>
					)}
				</div>
			</div>

			{session ? (
				<div className="pos-container">
					<div className="pos-catalog">
						<h3>Catalogo</h3>
						<div className="catalog-grid">
							{catalog.map((item) => (
								<div key={item.id} className="catalog-card">
									<h4>{item.name}</h4>
									<p className="price">{toMoney(item.price)} EUR</p>
									<button onClick={() => addToCart(item)} disabled={isPaymentPending}>Adicionar</button>
								</div>
							))}
						</div>
					</div>

					<div className="pos-cart">
						<h3>Carrinho</h3>
						<div className="cart-items">
							{cart.length ? (
								cart.map((line) => (
									<div key={line.item_id} className="cart-line">
										<div>
											<strong>{line.name}</strong>
											<div className="muted">{toMoney(line.price)} EUR</div>
										</div>
										<div className="line-total">
											x{line.qty} = {toMoney(line.price * line.qty)} EUR
										</div>
									</div>
								))
							) : (
								<p className="muted">O carrinho esta vazio</p>
							)}
						</div>

						<div className="cart-summary">
							<h4>Total a pagar: {toMoney(total)} EUR</h4>
						</div>

						<button className="pay-btn pay-btn-cash" onClick={payCash} disabled={loading || !cart.length || !config.permissions.canSell || isPaymentPending}>
							Pagar em Dinheiro
						</button>
						<button className="pay-btn pay-btn-eupago" onClick={payEupago} disabled={loading || !cart.length || !config.permissions.canSell || isPaymentPending}>
							Pagar com EuPago
						</button>
						<button className="pay-btn pay-btn-clear" onClick={clearCart} disabled={loading || !cart.length || isPaymentPending}>
							Limpar Carrinho
						</button>
					</div>
				</div>
			) : (
				<div className="view">
					<p>Abra uma sessao para comecar a vender.</p>
				</div>
			)}
		</div>
	);
}

function AdminRegisters({ config }: { config: BetterPOSConfig }) {
	const api = useMemo(() => createApi(config), [config]);
	const [rows, setRows] = useState<Register[]>([]);
	const [name, setName] = useState('');
	const [code, setCode] = useState('');
	const [error, setError] = useState('');

	function load() {
		api
			.registersList()
			.then((data) => setRows(data.registers || []))
			.catch((err: Error) => setError(err.message));
	}

	useEffect(() => {
		load();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	function create() {
		if (!name.trim() || !code.trim()) return;
		setError('');
		api
			.registerCreate({ name: name.trim(), code: code.trim(), currency: 'EUR' })
			.then(() => {
				setName('');
				setCode('');
				load();
			})
			.catch((err: Error) => setError(err.message));
	}

	function rename(row: Register) {
		const nextName = window.prompt('Nome da caixa', row.name);
		if (nextName === null) return;
		api
			.registerUpdate(row.id, {
				name: nextName,
				code: row.code,
				currency: row.currency,
				is_active: true,
			})
			.then(load)
			.catch((err: Error) => setError(err.message));
	}

	function deactivate(row: Register) {
		if (!window.confirm(`Desativar caixa ${row.name}?`)) return;
		api
			.registerDelete(row.id)
			.then(load)
			.catch((err: Error) => setError(err.message));
	}

	return (
		<div className="view">
			<Banner error={error} />
			<h3>Caixas</h3>
			<div className="card">
				<input value={name} onChange={(ev) => setName(ev.target.value)} placeholder="Nome" />{' '}
				<input value={code} onChange={(ev) => setCode(ev.target.value)} placeholder="Codigo" />{' '}
				<button onClick={create} disabled={!config.permissions.canManageRegisters}>
					Criar
				</button>
			</div>
			<div className="card">
				<table className="admin-table">
					<thead>
						<tr>
							<th>Nome</th>
							<th>Codigo</th>
							<th>Acoes</th>
						</tr>
					</thead>
					<tbody>
						{rows.map((row) => (
							<tr key={row.id}>
								<td>{row.name}</td>
								<td>{row.code}</td>
								<td>
									<button onClick={() => rename(row)} disabled={!config.permissions.canManageRegisters}>
										Editar
									</button>{' '}
									<button onClick={() => deactivate(row)} disabled={!config.permissions.canManageRegisters}>
										Desativar
									</button>
								</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}

function DataTableScreen({
	title,
	rows,
	columns,
	error,
}: {
	title: string;
	rows: TableRow[];
	columns: Array<{ key: string; label: string }>;
	error: string;
}) {
	return (
		<div className="view">
			<Banner error={error} />
			<h3>{title}</h3>
			<div className="card">
				<table className="admin-table">
					<thead>
						<tr>
							{columns.map((col) => (
								<th key={col.key}>{col.label}</th>
							))}
						</tr>
					</thead>
					<tbody>
						{rows.map((row, idx) => (
							<tr key={String(row.id || idx)}>
								{columns.map((col) => (
									<td key={col.key}>{String(row[col.key] ?? '')}</td>
								))}
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
}

function AdminDashboard({ config }: { config: BetterPOSConfig }) {
	const api = useMemo(() => createApi(config), [config]);
	const [report, setReport] = useState<ReportSummary | null>(null);
	const [sessions, setSessions] = useState<Session[]>([]);
	const [txs, setTxs] = useState<Transaction[]>([]);
	const [error, setError] = useState('');

	useEffect(() => {
		Promise.all([api.reportsSummary(1), api.sessionsList(), api.transactionsList()])
			.then(([r, s, t]) => {
				setReport(r);
				setSessions(s.sessions || []);
				setTxs(t.transactions || []);
			})
			.catch((err: Error) => setError(err.message));
	}, [api]);

	const openSessions = sessions.filter((s) => s.status === 'open').length;

	return (
		<div className="view">
			<Banner error={error} />
			<h3>Painel</h3>
			<div className="catalog-grid">
				<div className="card">
					<h4>Vendas de hoje</h4>
					<p>{toMoney(report?.total_sales || 0)} EUR</p>
					<p className="muted">{report?.total_count || 0} transacoes</p>
				</div>
				<div className="card">
					<h4>Sessoes abertas</h4>
					<p>{openSessions}</p>
					<p className="muted">Caixas ativas neste momento</p>
				</div>
				<div className="card">
					<h4>Transacoes recentes</h4>
					<p>{txs.length}</p>
					<p className="muted">Ultimas 200 carregadas</p>
				</div>
			</div>
		</div>
	);
}

function AdminReports({ config }: { config: BetterPOSConfig }) {
	const api = useMemo(() => createApi(config), [config]);
	const [days, setDays] = useState(30);
	const [report, setReport] = useState<ReportSummary | null>(null);
	const [error, setError] = useState('');

	useEffect(() => {
		setError('');
		api
			.reportsSummary(days)
			.then(setReport)
			.catch((err: Error) => setError(err.message));
	}, [api, days]);

	return (
		<div className="view">
			<Banner error={error} />
			<h3>Relatorios</h3>
			<div className="card">
				<label>Periodo (dias): </label>
				<select value={days} onChange={(ev) => setDays(Number(ev.target.value))}>
					<option value={7}>7</option>
					<option value={30}>30</option>
					<option value={90}>90</option>
				</select>
			</div>
			{report ? (
				<div className="card">
					<p>Total de vendas: {toMoney(report.total_sales)} EUR</p>
					<p>Transacoes: {report.total_count}</p>
					<ul>
						{(report.by_channel || []).map((ch) => (
							<li key={ch.channel}>
								{ch.label}: {toMoney(ch.total)} EUR ({ch.count})
							</li>
						))}
					</ul>
				</div>
			) : (
				<p>A carregar...</p>
			)}
		</div>
	);
}

function AdminScreen({ route, config }: { route: string; config: BetterPOSConfig }) {
	const api = useMemo(() => createApi(config), [config]);
	const [sessions, setSessions] = useState<Session[]>([]);
	const [txs, setTxs] = useState<Transaction[]>([]);
	const [auditRows, setAuditRows] = useState<AuditRow[]>([]);
	const [error, setError] = useState('');

	useEffect(() => {
		if (route.startsWith('/admin/sessions')) {
			api
				.sessionsList()
				.then((data) => setSessions(data.sessions || []))
				.catch((err: Error) => setError(err.message));
		}
		if (route.startsWith('/admin/transactions')) {
			api
				.transactionsList()
				.then((data) => setTxs(data.transactions || []))
				.catch((err: Error) => setError(err.message));
		}
		if (route.startsWith('/admin/audit')) {
			api
				.auditFeed()
				.then((data) => setAuditRows(data.actions || []))
				.catch((err: Error) => setError(err.message));
		}
	}, [api, route]);

	if (route.startsWith('/admin/dashboard')) {
		return <AdminDashboard config={config} />;
	}
	if (route.startsWith('/admin/registers')) {
		return <AdminRegisters config={config} />;
	}
	if (route.startsWith('/admin/sessions')) {
		return (
			<DataTableScreen
				title="Sessoes"
				error={error}
				rows={sessions as unknown as TableRow[]}
				columns={[
					{ key: 'id', label: 'ID' },
					{ key: 'register_name', label: 'Caixa' },
					{ key: 'status', label: 'Estado' },
					{ key: 'opened_at', label: 'Abertura' },
					{ key: 'difference', label: 'Diferenca' },
				]}
			/>
		);
	}
	if (route.startsWith('/admin/transactions')) {
		return (
			<DataTableScreen
				title="Transacoes"
				error={error}
				rows={txs as unknown as TableRow[]}
				columns={[
					{ key: 'order_code', label: 'Pedido' },
					{ key: 'amount', label: 'Valor' },
					{ key: 'channel', label: 'Canal' },
					{ key: 'state', label: 'Estado' },
					{ key: 'operator_name', label: 'Operador' },
					{ key: 'created_at', label: 'Criado em' },
				]}
			/>
		);
	}
	if (route.startsWith('/admin/audit')) {
		return (
			<DataTableScreen
				title="Auditoria"
				error={error}
				rows={auditRows as unknown as TableRow[]}
				columns={[
					{ key: 'action_type', label: 'Acao' },
					{ key: 'actor_id', label: 'Ator' },
					{ key: 'register_id', label: 'Caixa' },
					{ key: 'created_at', label: 'Criado em' },
				]}
			/>
		);
	}
	if (route.startsWith('/admin/reports')) {
		return <AdminReports config={config} />;
	}

	return <div className="view">Rota de gestao desconhecida</div>;
}

function AdminSubnav({ route, navigate }: { route: string; navigate: (route: string) => void }) {
	const tabs = [
		{ key: '/admin/dashboard', label: 'Painel' },
		{ key: '/admin/registers', label: 'Caixas' },
		{ key: '/admin/sessions', label: 'Sessoes' },
		{ key: '/admin/transactions', label: 'Transacoes' },
		{ key: '/admin/audit', label: 'Auditoria' },
		{ key: '/admin/reports', label: 'Relatorios' },
	];

	return (
		<div className="admin-subnav">
			<strong className="admin-subnav-title">Gestao</strong>
			<div className="admin-subnav-tabs">
				{tabs.map((tab) => {
					const active = route.indexOf(tab.key) === 0;
					return (
						<a
							key={tab.key}
							href="#"
							className={`admin-subnav-tab ${active ? 'active' : ''}`}
							onClick={(ev) => {
								ev.preventDefault();
								navigate(tab.key);
							}}
						>
							{tab.label}
						</a>
					);
				})}
			</div>
		</div>
	);
}

export default function App({ config }: AppProps) {
	const [route, navigate] = useAppRoute(config.basePath);
	const permissions = config.permissions;
	const canAdmin = !!(
		permissions.canManageRegisters || permissions.canViewAudit || permissions.canSessionControl
	);

	useEffect(() => {
		if (route === '/admin' && canAdmin) {
			navigate('/admin/dashboard');
		}
		if (route === '/admin' && !canAdmin) {
			navigate('/pos');
		}
	}, [canAdmin, navigate, route]);

	return (
		<div className="betterpos-container">
			<AppHeader navigate={navigate} canAdmin={canAdmin} />
			{route.startsWith('/admin') ? (
				canAdmin ? (
					<div>
						<AdminSubnav route={route} navigate={navigate} />
						<AdminScreen route={route} config={config} />
					</div>
				) : (
					<div className="view">
						<h3>Acesso negado</h3>
						<p>Nao tem permissao para aceder a area de gestao.</p>
					</div>
				)
			) : (
				<POSScreen config={config} />
			)}
		</div>
	);
}
