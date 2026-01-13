"""Stripe payment tools - payment links and refunds."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def payment_links_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a Stripe payment link.
    
    Args:
        args: Input with line_items, metadata
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        Payment link url and id
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
        link = stripe.PaymentLink.create(
            line_items=args["line_items"],
            metadata=args.get("metadata") or {},
        )
        
        return {
            "id": link.id,
            "url": link.url,
            "active": link.active,
        }
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))


def refunds_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a Stripe refund.
    
    Args:
        args: Input with payment_intent or charge id, optional amount
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        Refund id and status
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
        refund_params = {}
        
        if "payment_intent" in args:
            refund_params["payment_intent"] = args["payment_intent"]
        elif "charge" in args:
            refund_params["charge"] = args["charge"]
        else:
            raise RigToolRaised(ToolError(
                type="validation_error",
                message="Either payment_intent or charge is required",
                retryable=False,
            ))
        
        if "amount" in args:
            refund_params["amount"] = args["amount"]
        
        refund = stripe.Refund.create(**refund_params)
        
        return {
            "id": refund.id,
            "status": refund.status,
            "amount": refund.amount,
            "currency": refund.currency,
        }
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))

