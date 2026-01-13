"""Stripe subscription tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def subscriptions_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a Stripe subscription.
    
    Args:
        args: Input with customer_id, price_id, optional trial_days
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        Subscription id and status
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
        sub_params = {
            "customer": args["customer_id"],
            "items": [{"price": args["price_id"]}],
        }
        
        if args.get("trial_days"):
            sub_params["trial_period_days"] = args["trial_days"]
        
        subscription = stripe.Subscription.create(**sub_params)
        
        return {
            "id": subscription.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
        }
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))


def subscriptions_cancel(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Cancel a Stripe subscription.
    
    Args:
        args: Input with subscription_id
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        Subscription id and status
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
        subscription = stripe.Subscription.cancel(args["subscription_id"])
        
        return {
            "id": subscription.id,
            "status": subscription.status,
        }
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))

