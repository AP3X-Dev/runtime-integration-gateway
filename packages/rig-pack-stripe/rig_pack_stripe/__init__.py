"""RIG Pack: Stripe - Payment processing tools.

Provides tools for:
- Customer management
- Invoice creation
- Payment links
- Subscriptions
- Refunds

Auth: Requires STRIPE_API_KEY environment variable.
"""

from rig_pack_stripe.pack import PACK

__all__ = ["PACK"]

