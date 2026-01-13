# RIG Pack: Stripe

Payment processing tools for Stripe.

## Installation

```bash
rig install stripe
```

## Required Environment Variables

- `STRIPE_API_KEY` - Your Stripe API key

## Available Tools

| Tool | Risk | Description |
|------|------|-------------|
| `stripe.customers.create` | write | Create a new customer |
| `stripe.customers.search` | read | Search for customers |
| `stripe.invoices.create` | money | Create an invoice |
| `stripe.invoice_items.create` | money | Add item to invoice |
| `stripe.payment_links.create` | money | Create a payment link |
| `stripe.refunds.create` | money | Create a refund |
| `stripe.subscriptions.create` | money | Create a subscription |
| `stripe.subscriptions.cancel` | money | Cancel a subscription |

## Example Usage

```python
from rig_core import RigRuntime
from rig_core.rtp import CallContext

# Create a customer
result = runtime.call(
    "stripe.customers.create",
    {"email": "customer@example.com", "name": "John Doe"},
    CallContext(tenant_id="my-tenant")
)

if result.ok:
    print(f"Created customer: {result.output['id']}")
```

## Risk Classifications

- **read**: Read-only operations (search)
- **write**: Create/update operations
- **money**: Financial transactions (require approval by default)

