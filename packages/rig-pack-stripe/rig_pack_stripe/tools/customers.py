"""Stripe customer management tools."""

from __future__ import annotations

from typing import Any, Dict

from rig_core.rtp import CallContext, ToolError
from rig_core.runtime import RigToolRaised


def customers_create(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Create a new Stripe customer.
    
    Args:
        args: Input with email, name, phone, metadata
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        Customer id, email, name
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
        customer = stripe.Customer.create(
            email=args.get("email"),
            name=args.get("name"),
            phone=args.get("phone"),
            metadata=args.get("metadata") or {},
        )
        
        return {
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
        }
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))


def customers_search(
    args: Dict[str, Any], secrets: Dict[str, str], ctx: CallContext
) -> Dict[str, Any]:
    """Search for Stripe customers.
    
    Args:
        args: Input with query string
        secrets: Must contain STRIPE_API_KEY
        ctx: Call context
        
    Returns:
        List of matching customers
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
        result = stripe.Customer.search(query=args["query"])
        
        customers = []
        for c in result.data:
            customers.append({
                "id": c.id,
                "email": c.email,
                "name": c.name,
            })
        
        return {"customers": customers, "has_more": result.has_more}
    except stripe.StripeError as e:
        raise RigToolRaised(ToolError(
            type="upstream_error",
            message=str(e),
            upstream_code=getattr(e, "code", None),
            retryable=getattr(e, "should_retry", False),
        ))

