# BetterPOS - Point of Sale Plugin for Pretix

A modern, touch-first **Point of Sale** system for Pretix that provides a seamless experience for selling items at events.

## Features

🎯 **Touch-First Design**
- Optimized for tablets and touchscreens
- Large, responsive buttons
- Smooth interactions

💳 **Payment Processing**
- Cash payments
- euPago integration
- Transaction tracking
- Payment confirmations

📦 **Product Management**
- Real-time product catalog
- Dynamic pricing
- Product variations
- Quantity management

💰 **Cash Session Management**
- Open/close sessions with floats
- Cash movement tracking
- Session status monitoring
- Difference calculation

📊 **Reporting & Audit**
- Complete activity log
- Transaction history
- Operator tracking
- Audit trail

🔒 **Security**
- User authentication
- Permission-based access control
- Event scoping
- Idempotency protection

## Installation

### Prerequisites
- Pretix 4.7+ 
- Python 3.9+
- React 17+ (via CDN)

### Setup

1. **Install the plugin**
   ```bash
   pip install -e ./pretix-betterpos
   ```

2. **Run migrations**
   ```bash
   python manage.py migrate prettier_pos
   ```

3. **Create registers**
   - Go to Django admin for your event
   - Create register entries with unique codes
   - Set active status

4. **Assign permissions**
   - Add event staff as register operators
   - Grant POS permissions

5. **Access POS**
   ```
   http://localhost:8000/control/event/{organizer}/{event}/betterpos/
   ```

## Usage

### Opening a Session

1. Navigate to BetterPOS
2. Select a register from the list
3. Enter opening float (cash on hand)
4. Click "Open Session"

### Processing Sales

1. Browse the product catalog (left panel)
2. Click "Add" to add items to cart
3. Use +/- buttons to adjust quantities
4. Select payment method:
   - **Pay Cash** - for cash transactions
   - **Pay euPago** - for card/mobile payments
5. Confirm payment

### Closing Session

1. Click "Close Session" in the top navigation
2. Count the actual cash in register
3. Enter the count
4. Submit to close

## API Documentation

### REST Endpoints

**Session Management**
```
GET  /api/registers/                  - List available registers  
GET  /api/session/status/             - Check session status
POST /api/session/open/               - Open a cash session
POST /api/session/close/              - Close a cash session
POST /api/cash/movement/              - Record cash movement
```

**Catalog & Cart**
```
GET  /api/catalog/                    - Get product catalog
POST /api/cart/quote/                 - Calculate cart totals
```

**Orders & Payments**
```
POST /api/order/create/               - Create an order
POST /api/payment/cash/               - Process cash payment
POST /api/payment/eupago/             - Process euPago payment
POST /api/order/cancel/               - Cancel unpaid order
POST /api/order/refund/               - Refund a paid order
```

**Status & Audit**
```
GET  /api/transaction/{id}/status/    - Get transaction status
GET  /api/audit/feed/                 - Get activity log
```

## Architecture

### Frontend Stack
- **React 17** - via unpkg CDN (UMD)
- **CSS3** - fully responsive design
- **State Management** - React hooks (useState, useReducer)

### Backend Stack
- **Django 4.2+**
- **Django REST Framework** - API
- **PostgreSQL/SQLite** - database
- **Celery** - async tasks (optional)

### How It Works

```
┌──────────────┐
│  React App   │
└──────┬───────┘
       │ AJAX Requests
       ▼
┌──────────────────┐
│  REST API        │
│  /api/*          │
└──────┬───────────┘
       │ Django ORM
       ▼
┌──────────────┐
│  Database    │
└──────────────┘
```

## Permission Model

The plugin uses custom permissions:

| Permission | Purpose |
|-----------|---------|
| `can_view_pos` | View POS interface |
| `can_sell_pos` | Create orders and payments |
| `can_session_control_pos` | Open/close sessions |
| `can_cash_move_pos` | Record cash movements |
| `can_cancel_unpaid_pos` | Cancel unpaid orders |
| `can_refund_pos` | Refund paid orders |
| `can_view_audit_pos` | View activity log |

## Data Models

### BetterposRegister
Represents a physical register/till
- `event` - Associated event
- `name` - Display name
- `code` - Unique identifier
- `is_active` - Whether register is in use
- `default_currency` - Currency for transactions

### BetterposCashSession
Manages a cash session
- `register` - Associated register
- `opened_at` - Session start time
- `opened_by` - User who opened
- `opening_float` - Starting cash
- `status` - Current session status

### BetterposTransaction
Tracks a sale transaction
- `order` - Associated Pretix order
- `payment` - Associated payment
- `state` - Transaction state
- `channel` - Payment channel (cash/card)
- `operator` - User who made the sale

### BetterposCartSnapshot
Snapshots of shopping cart state
- `snapshot_payload` - Full cart JSON
- `expires_at` - When snapshot expires

### BetterposActionLog
Audit log entry
- `action_type` - What action occurred
- `actor` - User who performed action
- `payload` - Full details

## Configuration

### Django Settings

```python
# settings.py

# Register the plugin
INSTALLED_APPS = [
    # ...
    'pretix_betterpos',
]

# Optional: Configure defaults
PRETIX_BETTERPOS = {
    'DEFAULT_CURRENCY': 'EUR',
    'FLOAT_DECIMAL_PLACES': 2,
    'SESSION_TIMEOUT_HOURS': 24,
}
```

## Troubleshooting

### POS Page Blank
- Check browser console for errors
- Verify React CDN is accessible
- Check CSS file is loaded
- Ensure user has POS permissions

### Can't Open Session
- Verify registers exist for the event
- Check user has `can_session_control_pos` permission
- Make sure register is marked active

### Payments Failing
- Verify event has payment providers
- Check order/payment configuration
- Review Django logs for exceptions
- Ensure item prices are valid

## Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/pretixeu/pretix-betterpos.git
cd pretix-betterpos

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# Install dependencies
pip install -e .[dev]

# Run tests
python manage.py test
```

### Running Tests
```bash
# Run all tests
python manage.py test pretix_betterpos

# Run specific test
python manage.py test pretix_betterpos.tests.POSViewTests

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Submit a pull request

## Support

For issues and questions:

- 📖 [Documentation](./IMPLEMENTATION_GUIDE.md)
- 🧪 [Testing Guide](./QUICK_START_TESTING.md)
- 📝 [Implementation Details](./IMPLEMENTATION_SUMMARY.md)
- 💬 GitHub Issues

## License

GNU General Public License v3 (GPLv3)

See [LICENSE](./LICENSE) for details.

## Author

Developed for the Pretix community.

---

**Version:** 1.0.0  
**Status:** Production Ready ✅  
**Last Updated:** March 28, 2026
