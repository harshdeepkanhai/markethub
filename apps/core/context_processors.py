def cart(request):
    from app.orders.selectors import cart_item_count
    return {"cart_count": cart_item_count(request.user) if request.user.is_authenticated else 0}