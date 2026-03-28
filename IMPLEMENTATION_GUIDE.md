# BetterPOS Plugin - Implementation Guide

## Overview

BetterPOS is a complete **Point of Sale** system for Pretix that provides a modern, touch-friendly interface for selling items at events.

## Features Implemented

### ✅ Frontend (React)
- **Touch-first UI** optimized for tablets and touchscreens
- **Real-time state management** using React hooks (useState, useReducer)
- **Multiple views**:
  - Session Manager (register selection and session management)
  - POS Interface (catalog display, shopping cart)
  - Transaction Status (payment confirmation)
- **Responsive design** - works on desktop and mobile
- **Error handling** with user-friendly messages

### ✅ Shopping Cart
- Add items to cart from catalog
- Increment/decrement quantities
- Remove items
- Real-time total calculation
- Cart interface with line-by-line management

### ✅ Session Management
- Open/close cash sessions per register
- Opening floats
- Session status tracking
- Cash movement recording

### ✅ Payment Processing
- **Cash payments** - mark orders as paid in cash
- **euPago integration** - support for multiple payment methods
- Payment status tracking
- Transaction management

### ✅ API Endpoints
All REST API endpoints with proper authentication and permissions:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/registers/` | GET | List available registers |
| `/api/catalog/` | GET | Get product catalog |
| `/api/session/status/` | GET | Check session status |
| `/api/session/open/` | POST | Open a cash session |
| `/api/session/close/` | POST | Close a cash session |
| `/api/cash/movement/` | POST | Record cash movements |
| `/api/cart/quote/` | POST | Calculate cart totals |
| `/api/order/create/` | POST | Create an order |
| `/api/payment/cash/` | POST | Record cash payment |
| `/api/payment/eupago/` | POST | Initiate euPago payment |
| `/api/transaction/{id}/status/` | GET | Get transaction status |
| `/api/order/cancel/` | POST | Cancel unpaid order |
| `/api/order/refund/` | POST | Refund a paid order |
| `/api/audit/feed/` | GET | Get activity log |

### ✅ UI Components
1. **ErrorBox** - Display error messages
2. **Spinner** - Loading indicator
3. **Button** - Reusable button component with loading state
4. **CatalogGrid** - Display products in grid layout
5. **CartLine** - Individual cart item display with quantity controls
6. **SessionManagerView** - Register/session initialization
7. **POSView** - Main Point of Sale interface
8. **TransactionStatusView** - Payment confirmation modal

### ✅ Styling
- Professional CSS with mobile responsiveness
- Color scheme matching pretix standards
- Dark/light mode support via CSS variables
- Print-friendly styles
- Smooth transitions and animations

## Architecture

### State Management
```
BetterPOSApp (main component)
├── state.registers: BetterposRegister[]
├── state.session: Current session info
├── state.catalog: Product list
├── state.cart: CartLine[]
├── state.loading: boolean
├── state.error: Error message
├── state.processing: boolean
├── state.transaction: Transaction status
└── state.selectedRegister: Register ID
```

### Data Flow
```
User Actions → Handlers → API Calls → State Updates → UI Re-render
```

### API Integration
All API calls go through the `apiCall()` helper which:
- Handles authentication via cookies (same-origin)
- Sets proper Content-Type headers
- Parses JSON responses
- Throws on non-2xx status codes
- Returns JSON payload

## Installation & Setup

### Prerequisites
- Pretix development environment configured
- Python 3.12+
- Django 4.2+
- React 17+ (via CDN)

### Installation Steps

1. **Plugin Installation**
   ```bash
   cd /path/to/plugins
   pip install -e ./pretix-betterpos
   ```

2. **Django Setup**
   ```bash
   python manage.py migrate
   ```

3. **Create Registers** (Django admin)
   - Go to: `{event}/admin/` 
   - Create register entries with unique codes

4. **Assign Permissions**
   - Assign event staff to registers
   - Grant appropriate permissions

5. **Access POS Interface**
   - Navigate to: `/control/event/{organizer}/{event}/betterpos/`
   - React will load and render the interface

## Usage

### Daily Workflow

#### 1. Open Session
```
App Start → Select Register → Enter Opening Float → Open Session
```

#### 2. Make Sales
```
Browse Catalog → Add Items to Cart → Select Payment Method → Process
```

#### 3. Close Session
```
Click "Close Session" → Enter Counted Cash → Confirm
```

### For Sale Managers
- View all registers and their status
- Monitor cash sessions
- Access transaction history via audit feed
- Generate reports

### For Cashiers
- Simple POS interface optimized for touch
- Quick access to catalog
- One-click payments
- Transaction confirmation

## Security Features

### Authentication
- User must be logged in (checked in API)
- Django session authentication
- CSRF protection on all POST requests

### Permissions
- API validates permissions for each endpoint
- Custom POS permissions:
  - `can_view_pos` - View POS interface
  - `can_view_audit_pos` - View audit log
  - `can_sell_pos` - Create orders and payments
  - `can_session_control_pos` - Open/close sessions
  - `can_cash_move_pos` - Record cash movements
  - `can_cancel_unpaid_pos` - Cancel unpaid orders
  - `can_refund_pos` - Refund paid orders

### Data Protection
- Event scoping - users can only see their event's data
- Transaction logging - all actions are audited
- Idempotency keys - prevent duplicate orders

## Performance Optimization

### Frontend
- React hooks minimize re-renders
- useMemo for expensive calculations (totals)
- useCallback for stable function references
- Lazy loading of catalog

### Backend
- Database indexes on frequently queried fields
- Efficient ORM queries with select_related
- JSON-based API for minimal payload size
- Async session closure support

## Testing

### Manual Testing Checklist
- [ ] Open session with register
- [ ] View product catalog
- [ ] Add items to cart
- [ ] Increment/decrement quantities
- [ ] Remove items from cart
- [ ] Process cash payment
- [ ] Confirm transaction status
- [ ] Close session
- [ ] Verify audit log

### Error Scenarios
- [ ] No active session (should show error)
- [ ] Invalid payment type (should be rejected)
- [ ] Network error during payment (should retry)
- [ ] Session expires (should require re-login)

## API Response Examples

### Get Registers
```json
{
  "registers": [
    {"id": 1, "name": "Register A", "code": "reg-a", "currency": "EUR"},
    {"id": 2, "name": "Register B", "code": "reg-b", "currency": "EUR"}
  ]
}
```

### Get Catalog
```json
{
  "items": [
    {
      "id": 1,
      "name": "Adult Ticket",
      "price": "20.00",
      "variations": []
    }
  ]
}
```

### Create Order
```json
{
  "order_code": "ABCDE",
  "transaction": {
    "id": 42,
    "order_code": "ABCDE",
    "state": "order_created",
    "channel": "cash",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## Troubleshooting

### Frontend Not Loading
**Symptom:** Blank page, no React component visible

**Solution:**
1. Check browser console for errors
2. Verify React CDN is loading: `window.React` should exist
3. Check CSS file is loaded correctly

### API Calls Failing
**Symptom:** 403 Forbidden errors on API calls

**Solution:**
1. Verify user has POS permissions in event
2. Check `has_pos_permission()` in auth module
3. Ensure register is assigned to user

### Transactions Not Creating
**Symptom:** Orders don't appear in pretix

**Solution:**
1. Verify cart data is valid (prices, quantities)
2. Check OrderOrchestrationService parameters
3. Review Django logs for exceptions

## Future Enhancements

- [ ] Offline mode (PWA)
- [ ] Customer search and loyalty
- [ ] Complex discounts and promotions
- [ ] Receipt printing
- [ ] Split payments
- [ ] Advanced reporting and analytics
- [ ] Multiple payment provider integrations
- [ ] Inventory management
- [ ] Staff performance metrics

## Support & Documentation

- **API Documentation**: See `api/` folder
- **Models**: See `models/` folder
- **Services**: See `services/` folder
- **Frontend Code**: `static/pretixplugins/pretix_betterpos/`

## License

Same as Pretix (GPLv3)
