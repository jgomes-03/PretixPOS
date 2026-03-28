# BetterPOS - Quick Start & Testing Guide

## Getting Started (5 minutes)

### 1. Start the Development Server

```bash
cd e:\ISCTE\NET\Pretix\pretix-dev\src
python manage.py runserver
```

The server will start at: `http://localhost:8000`

### 2. Login to Pretix
- URL: `http://localhost:8000/`
- Username: admin (or your user)
- Password: your password

### 3. Access BetterPOS
Navigate to: 
```
http://localhost:8000/control/event/net-dev/comer-reitora/betterpos/
```

(Replace `net-dev` with organizer slug and `comer-reitora` with event slug)

## Testing the Interface

### Test Case 1: Open Session
1. You should see **Session Manager** screen
2. Click on an available register (e.g., "Caixa 1")
3. Enter opening float (e.g., "10.00")
4. Click "Open Session"
5. ✅ You should see the **POS Interface** with catalog and cart

### Test Case 2: Add Items to Cart
1. In the **POS Interface**, browse the catalog on the left
2. Click "Add" on any product
3. The item should appear in the cart on the right
4. Total should update in real-time

### Test Case 3: Manage Cart
1. In the cart section, use `-` and `+` buttons to change quantity
2. Click "Remove" to delete an item
3. Total updates automatically

### Test Case 4: Process Payment
1. With items in cart, click "Pay Cash"
2. System creates order and records payment
3. You should see **Transaction Status** modal
4. Shows order code and payment status
5. Click "Close" to return to POS

### Test Case 5: Close Session
1. Click "Close Session" button in POS header
2. You return to **Session Manager**
3. Session is now closed

## Debugging

### Browser Console
Press `F12` to open Developer Tools Console. Look for:

```javascript
// Check if React loaded
window.React !== undefined  // Should be true

// Check if API calls are working
fetch('/api/registers/', {credentials: 'same-origin'})
  .then(r => r.json())
  .then(d => console.log(d))  // Check response
```

### Network Tab
Check that these API calls succeed (status 200):
- `GET /api/registers/`
- `POST /api/session/open/`
- `GET /api/catalog/`
- `POST /api/order/create/`
- `POST /api/payment/cash/`

### Django Logs
Watch the terminal where `runserver` is running for errors.

### Database Queries
Check Django admin:
```
http://localhost:8000/control/event/net-dev/comer-reitora/admin/betterpos_betterpos_register/
```

Should show created registers.

## Common Issues & Solutions

### Issue 1: "No registers available"
**Cause:** No registers created for the event

**Solution:**
1. Go to Django admin
2. Create a register:
   - Name: "Caixa 1"
   - Code: "caixa-1"
   - Active: Yes
3. Refresh BetterPOS page

### Issue 2: Page shows blank
**Cause:** React CDN not loading

**Solution:**
1. Check browser console for errors
2. Verify React UMD CDN is accessible
3. Check network tab for CDN requests
4. If blocked, the fallback UI should still appear

### Issue 3: Can't open session
**Cause:** Missing POS permissions

**Solution:**
1. Go to event Settings → Permissions
2. Assign POS permissions to your user
3. Log out and back in
4. Refresh BetterPOS page

### Issue 4: Payment fails
**Cause:** Order creation error

**Solution:**
1. Check browser console for error details
2. Verify items exist in catalog
3. Check Django logs for exceptions
4. Ensure event has payment providers configured

## What to Test

### Core Features
- [ ] Session management (open/close)
- [ ] Catalog loading and display
- [ ] Add/remove items from cart
- [ ] Quantity management
- [ ] Total calculation
- [ ] Cash payments
- [ ] Transaction tracking
- [ ] Error handling

### User Experience
- [ ] Touch-friendly buttons (large enough)
- [ ] Responsive layout on different screen sizes
- [ ] Clear error messages
- [ ] Loading states
- [ ] Performance (quick operations)

### Data Integrity
- [ ] Orders created correctly in pretix
- [ ] Payments recorded
- [ ] Session cash calculations
- [ ] Audit logs populated

## Performance Testing

### Load Time
Measure time to first interaction:
1. Open BetterPOS URL
2. Check time until POS is interactive
3. Should be < 3 seconds

### Responsiveness
Test 50 items in cart:
1. Add 50 different items
2. Modify quantities rapidly
3. Check for lag or delays
4. Total should update smoothly

## Verification Checklist

Before considering development complete:

- [ ] Django `manage.py check` passes
- [ ] No JavaScript errors in console
- [ ] All API endpoints respond correctly
- [ ] User can open/close sessions
- [ ] User can add items to cart
- [ ] User can process payments
- [ ] Transactions appear in pretix
- [ ] UI is responsive
- [ ] No database migrations needed

## Next Steps

After testing passes:

1. **Create Test Orders** - Process several test orders
2. **Verify in pretix** - Check orders in pretix admin
3. **Test Refunds** - Refund a paid order
4. **Check Audit Log** - Verify all actions logged
5. **Test on Mobile** - Test on actual touchscreen tablet

## Useful Commands

```bash
# Fresh database for testing
python manage.py migrate

# Create test data
python manage.py createsuperuser

# Run tests
python manage.py test

# Shell for debugging
python manage.py shell

# View logs in real-time
tail -f pretix.log
```

## Support

If issues arise:

1. Check browser console (F12)
2. Check Django logs in terminal
3. Check database admin interface
4. Read IMPLEMENTATION_GUIDE.md for architecture details
