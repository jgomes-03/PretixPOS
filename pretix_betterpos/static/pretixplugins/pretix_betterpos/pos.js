(function () {
  var React = window.React;
  var ReactDOM = window.ReactDOM;
  var cfg = window.BETTERPOS || {};
  var mountNode = document.getElementById('betterpos-app');

  function isMissing(v) {
    return v === undefined || v === null || v === '' || v === 'undefined' || v === 'None' || v === 'null';
  }

  function parseEventContextFromPath(pathname) {
    var m = pathname.match(/^\/control\/event\/([^/]+)\/([^/]+)\//);
    if (!m) return null;
    return { organizer: m[1], event: m[2] };
  }

  function asBool(v) {
    return v === true || v === 'true' || v === '1' || v === 1;
  }

  function normalizeConfig() {
    var ds = mountNode && mountNode.dataset ? mountNode.dataset : {};

    if (isMissing(cfg.organizer) && !isMissing(ds.organizer)) cfg.organizer = ds.organizer;
    if (isMissing(cfg.event) && !isMissing(ds.event)) cfg.event = ds.event;
    if (isMissing(cfg.basePath) && !isMissing(ds.basePath)) cfg.basePath = ds.basePath;
    if (isMissing(cfg.apiBase) && !isMissing(ds.apiBase)) cfg.apiBase = ds.apiBase;

    var parsed = parseEventContextFromPath(window.location.pathname);
    if (parsed) {
      if (isMissing(cfg.organizer)) cfg.organizer = parsed.organizer;
      if (isMissing(cfg.event)) cfg.event = parsed.event;
      if (isMissing(cfg.basePath)) {
        cfg.basePath = '/control/event/' + parsed.organizer + '/' + parsed.event + '/betterpos';
      }
    }

    if (isMissing(cfg.apiBase) && !isMissing(cfg.basePath)) {
      cfg.apiBase = String(cfg.basePath).replace(/\/$/, '') + '/api';
    }

    if (!cfg.permissions || typeof cfg.permissions !== 'object') {
      cfg.permissions = {
        canManageRegisters: asBool(ds.canManageRegisters),
        canViewAudit: asBool(ds.canViewAudit),
        canSessionControl: asBool(ds.canSessionControl),
        canSell: asBool(ds.canSell)
      };
    }
  }

  if (!React || !ReactDOM || !mountNode) {
    document.body.innerHTML = '<p style="color:red;padding:20px;">React failed to initialize.</p>';
    return;
  }

  normalizeConfig();

  var e = React.createElement;
  var useState = React.useState;
  var useEffect = React.useEffect;
  var useMemo = React.useMemo;

  function toMoney(value) {
    var n = Number(value);
    if (Number.isNaN(n)) return '0.00';
    return n.toFixed(2);
  }

  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i += 1) {
        var cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + '=') {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function jsonFetch(url, options) {
    var opts = options || {};
    var method = (opts.method || 'GET').toUpperCase();
    opts.credentials = 'same-origin';
    opts.headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});

    if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS' && method !== 'TRACE') {
      var csrfToken = getCookie('csrftoken');
      if (csrfToken) {
        opts.headers['X-CSRFToken'] = csrfToken;
      }
    }

    return fetch(url, opts).then(function (res) {
      return res.text().then(function (raw) {
        var data = {};
        try {
          data = raw ? JSON.parse(raw) : {};
        } catch (err) {
          data = { error: raw || 'Invalid response' };
        }
        if (!res.ok) {
          throw new Error(data.error || ('HTTP ' + res.status));
        }
        return data;
      });
    });
  }

  var api = {
    registersList: function () { return jsonFetch(cfg.apiBase + '/registers/'); },
    registerCreate: function (payload) {
      return jsonFetch(cfg.apiBase + '/registers/', { method: 'POST', body: JSON.stringify(payload) });
    },
    registerUpdate: function (id, payload) {
      return jsonFetch(cfg.apiBase + '/registers/' + id + '/', { method: 'PUT', body: JSON.stringify(payload) });
    },
    registerDelete: function (id) {
      return jsonFetch(cfg.apiBase + '/registers/' + id + '/', { method: 'DELETE' });
    },
    sessionStatus: function (registerId) { return jsonFetch(cfg.apiBase + '/session/status/?register_id=' + registerId); },
    sessionOpen: function (payload) { return jsonFetch(cfg.apiBase + '/session/open/', { method: 'POST', body: JSON.stringify(payload) }); },
    sessionClose: function (payload) { return jsonFetch(cfg.apiBase + '/session/close/', { method: 'POST', body: JSON.stringify(payload) }); },
    sessionsList: function () { return jsonFetch(cfg.apiBase + '/sessions/?limit=100'); },
    catalog: function () { return jsonFetch(cfg.apiBase + '/catalog/'); },
    orderCreate: function (payload) { return jsonFetch(cfg.apiBase + '/order/create/', { method: 'POST', body: JSON.stringify(payload) }); },
    payCash: function (payload) { return jsonFetch(cfg.apiBase + '/payment/cash/', { method: 'POST', body: JSON.stringify(payload) }); },
    transactionsList: function () { return jsonFetch(cfg.apiBase + '/transactions/?limit=200'); },
    auditFeed: function () { return jsonFetch(cfg.apiBase + '/audit/feed/?limit=200'); },
    reportsSummary: function (days) { return jsonFetch(cfg.apiBase + '/reports/summary/?days=' + days); }
  };

  function pathFromLocation() {
    var base = (cfg.basePath || '').replace(/\/$/, '');
    var current = window.location.pathname;
    if (!base || current === base || current === base + '/') return '/pos';
    if (current.indexOf(base + '/') === 0) {
      var sub = current.slice(base.length);
      return sub || '/pos';
    }
    return '/pos';
  }

  function useAppRoute() {
    var _a = useState(pathFromLocation());
    var route = _a[0];
    var setRoute = _a[1];

    useEffect(function () {
      function onPop() {
        setRoute(pathFromLocation());
      }
      window.addEventListener('popstate', onPop);
      return function () { window.removeEventListener('popstate', onPop); };
    }, []);

    function navigate(nextRoute) {
      var normalized = nextRoute.charAt(0) === '/' ? nextRoute : '/' + nextRoute;
      var target = (cfg.basePath || '') + normalized;
      window.history.pushState({}, '', target);
      setRoute(normalized);
    }

    return [route, navigate];
  }

  function Banner(props) {
    if (!props.error) return null;
    return e('div', { className: 'error-box' }, props.error);
  }

  function AppHeader(props) {
    return e(
      'header',
      { className: 'betterpos-header' },
      e('h1', null, 'BetterPOS'),
      e(
        'nav',
        null,
        e(
          'a',
          {
            href: '#',
            onClick: function (ev) {
              ev.preventDefault();
              props.navigate('/pos');
            }
          },
          'Frontoffice'
        ),
        props.canAdmin
          ? e(
              'a',
              {
                href: '#',
                onClick: function (ev) {
                  ev.preventDefault();
                  props.navigate('/admin/dashboard');
                }
              },
              'Backoffice'
            )
          : null
      )
    );
  }

  function POSScreen(props) {
    var _a = useState([]);
    var registers = _a[0];
    var setRegisters = _a[1];

    var _b = useState(null);
    var selectedRegister = _b[0];
    var setSelectedRegister = _b[1];

    var _c = useState(null);
    var session = _c[0];
    var setSession = _c[1];

    var _d = useState([]);
    var catalog = _d[0];
    var setCatalog = _d[1];

    var _e = useState([]);
    var cart = _e[0];
    var setCart = _e[1];

    var _f = useState(false);
    var loading = _f[0];
    var setLoading = _f[1];

    var _g = useState('');
    var error = _g[0];
    var setError = _g[1];

    function refreshRegisters() {
      setLoading(true);
      setError('');
      api.registersList()
        .then(function (data) {
          setRegisters(data.registers || []);
          if ((data.registers || []).length && !selectedRegister) {
            setSelectedRegister((data.registers || [])[0]);
          }
        })
        .catch(function (err) { setError(err.message); })
        .finally(function () { setLoading(false); });
    }

    useEffect(function () { refreshRegisters(); }, []);

    useEffect(function () {
      if (!selectedRegister) return;
      api.sessionStatus(selectedRegister.id)
        .then(function (data) {
          if (data.has_open_session) {
            setSession({
              id: data.session.id,
              register_id: selectedRegister.id,
              register_name: selectedRegister.name,
              status: 'open'
            });
            return api.catalog();
          }
          setSession(null);
          return null;
        })
        .then(function (catalogData) {
          if (catalogData && catalogData.items) setCatalog(catalogData.items);
        })
        .catch(function (err) {
          setError(err.message);
        });
    }, [selectedRegister && selectedRegister.id]);

    function openSession() {
      if (!selectedRegister) return;
      var amount = window.prompt('Opening float', '0.00');
      if (amount === null) return;
      setLoading(true);
      setError('');
      api.sessionOpen({ register_id: selectedRegister.id, opening_float: amount })
        .then(function (data) {
          setSession({
            id: data.session_id,
            register_id: selectedRegister.id,
            register_name: selectedRegister.name,
            status: data.status
          });
          return api.catalog();
        })
        .then(function (catalogData) {
          setCatalog(catalogData.items || []);
        })
        .catch(function (err) { setError(err.message); })
        .finally(function () { setLoading(false); });
    }

    function closeSession() {
      if (!session) return;
      var counted = window.prompt('Counted cash', '0.00');
      if (counted === null) return;
      setLoading(true);
      api.sessionClose({ register_id: session.register_id, counted_cash: counted })
        .then(function () {
          setSession(null);
          setCart([]);
        })
        .catch(function (err) { setError(err.message); })
        .finally(function () { setLoading(false); });
    }

    function addToCart(item) {
      setCart(function (old) {
        var existing = old.find(function (line) { return line.item_id === item.id; });
        if (existing) {
          return old.map(function (line) {
            return line.item_id === item.id ? Object.assign({}, line, { qty: line.qty + 1 }) : line;
          });
        }
        return old.concat([{ item_id: item.id, name: item.name, price: Number(item.price || 0), qty: 1 }]);
      });
    }

    function payCash() {
      if (!session || !cart.length) return;
      setLoading(true);
      setError('');
      var lines = cart.map(function (c) { return { item_id: c.item_id, quantity: c.qty }; });
      api.orderCreate({ register_id: session.register_id, lines: lines })
        .then(function (data) {
          return api.payCash({ transaction_id: data.transaction.id });
        })
        .then(function () {
          setCart([]);
          window.alert('Payment completed.');
        })
        .catch(function (err) { setError(err.message); })
        .finally(function () { setLoading(false); });
    }

    var total = useMemo(function () {
      return cart.reduce(function (acc, line) { return acc + line.price * line.qty; }, 0);
    }, [cart]);

    return e(
      'div',
      { className: 'view pos-view' },
      e(Banner, { error: error }),
      e(
        'div',
        { className: 'pos-header' },
        e(
          'div',
          null,
          e('strong', null, 'Register: '),
          selectedRegister ? selectedRegister.name : 'None selected',
          ' ',
          loading ? '(loading...)' : ''
        ),
        e(
          'div',
          null,
          e(
            'select',
            {
              value: selectedRegister ? selectedRegister.id : '',
              onChange: function (ev) {
                var id = Number(ev.target.value);
                var reg = registers.find(function (r) { return r.id === id; });
                setSelectedRegister(reg || null);
              }
            },
            e('option', { value: '' }, 'Select register'),
            registers.map(function (reg) { return e('option', { key: reg.id, value: reg.id }, reg.name + ' (' + reg.code + ')'); })
          ),
          ' ',
          session
            ? e('button', { onClick: closeSession, disabled: loading }, 'Close session')
            : e('button', { onClick: openSession, disabled: !selectedRegister || loading }, 'Open session')
        )
      ),
      session
        ? e(
            'div',
            { className: 'pos-container' },
            e(
              'div',
              { className: 'pos-catalog' },
              e('h3', null, 'Catalog'),
              e(
                'div',
                { className: 'catalog-grid' },
                catalog.map(function (item) {
                  return e(
                    'div',
                    { key: item.id, className: 'catalog-card' },
                    e('h4', null, item.name),
                    e('p', { className: 'price' }, '$' + toMoney(item.price)),
                    e('button', { onClick: function () { addToCart(item); } }, 'Add')
                  );
                })
              )
            ),
            e(
              'div',
              { className: 'pos-cart' },
              e('h3', null, 'Cart'),
              e(
                'div',
                { className: 'cart-items' },
                cart.length
                  ? cart.map(function (line) {
                      return e(
                        'div',
                        { key: line.item_id, className: 'cart-line' },
                        e('div', null, e('strong', null, line.name), e('div', { className: 'muted' }, '$' + toMoney(line.price))),
                        e('div', { className: 'line-total' }, 'x' + line.qty + ' = $' + toMoney(line.price * line.qty))
                      );
                    })
                  : e('p', { className: 'muted' }, 'Cart is empty')
              ),
              e('div', { className: 'cart-summary' }, e('h4', null, 'Total: $' + toMoney(total))),
              e('button', { onClick: payCash, disabled: loading || !cart.length }, 'Pay Cash'),
              e('button', {
                onClick: function () { setCart([]); },
                disabled: loading || !cart.length,
                style: { marginTop: '8px' }
              }, 'Clear Cart')
            )
          )
        : e('div', { className: 'view' }, e('p', null, 'Open a session to start selling.'))
    );
  }

  function AdminRegisters() {
    var _a = useState([]);
    var rows = _a[0];
    var setRows = _a[1];

    var _b = useState('');
    var name = _b[0];
    var setName = _b[1];

    var _c = useState('');
    var code = _c[0];
    var setCode = _c[1];

    var _d = useState('');
    var error = _d[0];
    var setError = _d[1];

    function load() {
      api.registersList().then(function (data) { setRows(data.registers || []); }).catch(function (err) { setError(err.message); });
    }

    useEffect(function () { load(); }, []);

    function create() {
      if (!name.trim() || !code.trim()) return;
      setError('');
      api.registerCreate({ name: name.trim(), code: code.trim(), currency: 'EUR' })
        .then(function () {
          setName('');
          setCode('');
          load();
        })
        .catch(function (err) { setError(err.message); });
    }

    function rename(row) {
      var nextName = window.prompt('Register name', row.name);
      if (nextName === null) return;
      api.registerUpdate(row.id, { name: nextName, code: row.code, currency: row.currency, is_active: true })
        .then(load)
        .catch(function (err) { setError(err.message); });
    }

    function deactivate(row) {
      if (!window.confirm('Deactivate register ' + row.name + '?')) return;
      api.registerDelete(row.id).then(load).catch(function (err) { setError(err.message); });
    }

    return e(
      'div',
      { className: 'view' },
      e(Banner, { error: error }),
      e('h3', null, 'Registers'),
      e('div', { className: 'card' },
        e('input', { value: name, onChange: function (ev) { setName(ev.target.value); }, placeholder: 'Name' }),
        ' ',
        e('input', { value: code, onChange: function (ev) { setCode(ev.target.value); }, placeholder: 'Code' }),
        ' ',
        e('button', { onClick: create }, 'Create')
      ),
      e('div', { className: 'card' },
        e('table', { className: 'admin-table' },
          e('thead', null, e('tr', null, e('th', null, 'Name'), e('th', null, 'Code'), e('th', null, 'Actions'))),
          e('tbody', null,
            rows.map(function (row) {
              return e('tr', { key: row.id },
                e('td', null, row.name),
                e('td', null, row.code),
                e('td', null,
                  e('button', { onClick: function () { rename(row); } }, 'Edit'),
                  ' ',
                  e('button', { onClick: function () { deactivate(row); } }, 'Deactivate')
                )
              );
            })
          )
        )
      )
    );
  }

  function DataTableScreen(props) {
    return e(
      'div',
      { className: 'view' },
      e(Banner, { error: props.error }),
      e('h3', null, props.title),
      e('div', { className: 'card' },
        e('table', { className: 'admin-table' },
          e('thead', null, e('tr', null, props.columns.map(function (col) { return e('th', { key: col.key }, col.label); }))),
          e('tbody', null,
            (props.rows || []).map(function (row, idx) {
              return e('tr', { key: row.id || idx },
                props.columns.map(function (col) {
                  return e('td', { key: col.key }, String(row[col.key] == null ? '' : row[col.key]));
                })
              );
            })
          )
        )
      )
    );
  }

  function AdminReports() {
    var _a = useState(30);
    var days = _a[0];
    var setDays = _a[1];

    var _b = useState(null);
    var report = _b[0];
    var setReport = _b[1];

    var _c = useState('');
    var error = _c[0];
    var setError = _c[1];

    useEffect(function () {
      setError('');
      api.reportsSummary(days).then(setReport).catch(function (err) { setError(err.message); });
    }, [days]);

    return e(
      'div',
      { className: 'view' },
      e(Banner, { error: error }),
      e('h3', null, 'Reports'),
      e('div', { className: 'card' },
        e('label', null, 'Period (days): '),
        e('select', { value: days, onChange: function (ev) { setDays(Number(ev.target.value)); } },
          e('option', { value: 7 }, '7'),
          e('option', { value: 30 }, '30'),
          e('option', { value: 90 }, '90')
        )
      ),
      report ? e('div', { className: 'card' },
        e('p', null, 'Total sales: $' + toMoney(report.total_sales)),
        e('p', null, 'Transactions: ' + report.total_count),
        e('ul', null,
          (report.by_channel || []).map(function (ch) {
            return e('li', { key: ch.channel }, ch.label + ': $' + toMoney(ch.total) + ' (' + ch.count + ')');
          })
        )
      ) : e('p', null, 'Loading...')
    );
  }

  function AdminScreen(props) {
    var route = props.route;

    var _a = useState([]);
    var sessions = _a[0];
    var setSessions = _a[1];

    var _b = useState([]);
    var txs = _b[0];
    var setTxs = _b[1];

    var _c = useState([]);
    var auditRows = _c[0];
    var setAuditRows = _c[1];

    var _d = useState('');
    var error = _d[0];
    var setError = _d[1];

    useEffect(function () {
      if (route.indexOf('/admin/sessions') === 0) {
        api.sessionsList().then(function (data) { setSessions(data.sessions || []); }).catch(function (err) { setError(err.message); });
      }
      if (route.indexOf('/admin/transactions') === 0) {
        api.transactionsList().then(function (data) { setTxs(data.transactions || []); }).catch(function (err) { setError(err.message); });
      }
      if (route.indexOf('/admin/audit') === 0) {
        api.auditFeed().then(function (data) { setAuditRows(data.actions || []); }).catch(function (err) { setError(err.message); });
      }
    }, [route]);

    if (route.indexOf('/admin/registers') === 0 || route.indexOf('/admin/dashboard') === 0) {
      return e(AdminRegisters);
    }
    if (route.indexOf('/admin/sessions') === 0) {
      return e(DataTableScreen, {
        title: 'Sessions',
        error: error,
        rows: sessions,
        columns: [
          { key: 'id', label: 'ID' },
          { key: 'register_name', label: 'Register' },
          { key: 'status', label: 'Status' },
          { key: 'opened_at', label: 'Opened' },
          { key: 'difference', label: 'Difference' }
        ]
      });
    }
    if (route.indexOf('/admin/transactions') === 0) {
      return e(DataTableScreen, {
        title: 'Transactions',
        error: error,
        rows: txs,
        columns: [
          { key: 'order_code', label: 'Order' },
          { key: 'amount', label: 'Amount' },
          { key: 'channel', label: 'Channel' },
          { key: 'state', label: 'State' },
          { key: 'operator_name', label: 'Operator' },
          { key: 'created_at', label: 'Created' }
        ]
      });
    }
    if (route.indexOf('/admin/audit') === 0) {
      return e(DataTableScreen, {
        title: 'Audit',
        error: error,
        rows: auditRows,
        columns: [
          { key: 'action_type', label: 'Action' },
          { key: 'actor_id', label: 'Actor' },
          { key: 'register_id', label: 'Register' },
          { key: 'created_at', label: 'Created' }
        ]
      });
    }
    if (route.indexOf('/admin/reports') === 0) {
      return e(AdminReports);
    }

    return e('div', { className: 'view' }, 'Unknown admin route');
  }

  function AdminSubnav(props) {
    var tabs = [
      { key: '/admin/dashboard', label: 'Dashboard' },
      { key: '/admin/registers', label: 'Registers' },
      { key: '/admin/sessions', label: 'Sessions' },
      { key: '/admin/transactions', label: 'Transactions' },
      { key: '/admin/audit', label: 'Audit' },
      { key: '/admin/reports', label: 'Reports' }
    ];

    return e(
      'div',
      { className: 'pos-header' },
      e('strong', null, 'Backoffice'),
      e(
        'div',
        null,
        tabs.map(function (tab) {
          var active = props.route.indexOf(tab.key) === 0;
          return e(
            'a',
            {
              key: tab.key,
              href: '#',
              onClick: function (ev) {
                ev.preventDefault();
                props.navigate(tab.key);
              },
              style: {
                marginLeft: '8px',
                padding: '6px 10px',
                borderRadius: '6px',
                background: active ? '#2d7f5e' : '#ececec',
                color: active ? '#fff' : '#333',
                textDecoration: 'none'
              }
            },
            tab.label
          );
        })
      )
    );
  }

  function BetterPOSApp() {
    var _a = useAppRoute();
    var route = _a[0];
    var navigate = _a[1];

    var permissions = cfg.permissions || {};
    var canAdmin = !!(permissions.canManageRegisters || permissions.canViewAudit || permissions.canSessionControl);

    useEffect(function () {
      if (route === '/admin' && canAdmin) {
        navigate('/admin/dashboard');
      }
      if (route === '/admin' && !canAdmin) {
        navigate('/pos');
      }
    }, []);

    return e(
      'div',
      { className: 'betterpos-container' },
      e(AppHeader, { navigate: navigate, canAdmin: canAdmin }),
      route.indexOf('/admin') === 0
        ? canAdmin
          ? e('div', null, e(AdminSubnav, { route: route, navigate: navigate }), e(AdminScreen, { route: route }))
          : e('div', { className: 'view' }, e('h3', null, 'Access denied'), e('p', null, 'You do not have permission to access backoffice.'))
        : e(POSScreen, { navigate: navigate })
    );
  }

  ReactDOM.render(e(BetterPOSApp), mountNode);
})();
