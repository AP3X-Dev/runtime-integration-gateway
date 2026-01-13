"""Stripe invoice tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def invoices_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a new Stripe invoice.
    
    Args:
        args: Input with customer_id, collection_method, days_until_due
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        Invoice id and status
    """
    import stripe
    
    api_key = secrets.get("STRIPE_API_KEY")
    if not api_key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="STRIPE_API_KEY not configured",
            retryable=False,
        ))
    
    stripe.api_key = api_key
    
    try:
        invoice = stripe.Invoice.create(
            customer=args["customer_id"],
            collection_method=args.get("collection_method", "charge_automatically"),
            days_until_due=args.get("days_until_due"),
            auto_advance=args.get("auto_advance", True),
        )
        
        return {
            "id": invoice.id,
            "status": invoice.status,
            "total": invoice.total,
            "currency": invoice.currency,
        }
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))


def invoice_items_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Add an item to a Stripe invoice.
    
    Args:
        args: Input with customer_id, amount, currency, description
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        Invoice item id
    """
    import stripe
    
    api_key = secrets.get("STRIPE_API_KEY")
    if not api_key:
        raise RigToolRaised(ToolError(
            type="auth_error",
            message="STRIPE_API_KEY not configured",
            retryable=False,
        ))
    
    stripe.api_key = api_key
    
    try:
        item = stripe.InvoiceItem.create(
            customer=args["customer_id"],
            amount=args["amount"],
            currency=args.get("currency", "usd"),
            description=args.get("description"),
            invoice=args.get("invoice_id"),
        )
        
        return {
            "id": item.id,
            "amount": item.amount,
            "currency": item.currency,
        }
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))

