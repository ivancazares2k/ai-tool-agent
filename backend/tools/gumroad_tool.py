import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.gumroad.com/v2"


def _token() -> str:
    """Retrieve Gumroad access token from environment."""
    token = os.getenv("GUMROAD_ACCESS_TOKEN")
    if not token:
        raise ValueError("GUMROAD_ACCESS_TOKEN environment variable not set.")
    return token


def _auth() -> dict:
    """Return auth params dict for Gumroad API requests."""
    return {"access_token": _token()}


async def get_products() -> str:
    """
    Retrieve all products in the Gumroad store.

    Returns:
        A formatted string listing all products with ID, name, price, and status
    """
    try:
        response = requests.get(f"{BASE_URL}/products", params=_auth())
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        products = data.get("products", [])
        if not products:
            return "No products found in your Gumroad store."

        lines = [f"ShipStack products ({len(products)} total):\n"]
        for p in products:
            price = f"${p.get('price', 0) / 100:.2f}"
            published = "✅ live" if p.get("published") else "⏸ unpublished"
            sales = p.get("sales_count", 0)
            lines.append(
                f"ID: {p.get('id') or p.get('external_id', 'N/A')}\n"
                f"Name: {p['name']}\n"
                f"Price: {price} — {published} — {sales} sales"
            )

        return "\n---\n".join(lines)

    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_product(product_id: str) -> str:
    """
    Retrieve details for a single Gumroad product.

    Args:
        product_id: The Gumroad product ID

    Returns:
        A formatted string with full product details
    """
    try:
        response = requests.get(f"{BASE_URL}/products/{product_id}", params=_auth())
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        p = data.get("product", {})
        price = f"${p.get('price', 0) / 100:.2f}"
        published = "✅ live" if p.get("published") else "⏸ unpublished"

        return (
            f"Name: {p.get('name')}\n"
            f"ID: {p.get('id')}\n"
            f"Price: {price}\n"
            f"Status: {published}\n"
            f"Sales: {p.get('sales_count', 0)}\n"
            f"URL: {p.get('short_url', '')}\n"
            f"Description: {p.get('description', '').strip()}"
        )

    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def create_product(name: str, price_cents: int, description: str = "") -> str:
    """
    Create a new product listing on Gumroad.

    Args:
        name: Product name
        price_cents: Price in cents (e.g. 2499 for $24.99). Use 0 for free.
        description: Product description (optional)

    Returns:
        Confirmation string with the new product ID and URL
    """
    try:
        params = {**_auth(), "name": name, "price": price_cents}
        if description:
            params["description"] = description

        response = requests.post(f"{BASE_URL}/products", params=params)
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        p = data.get("product", {})
        return (
            f"Product created: '{p.get('name')}'\n"
            f"ID: {p.get('id')}\n"
            f"URL: {p.get('short_url', '')}\n"
            f"Status: unpublished — enable it when ready to sell."
        )

    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def update_product(product_id: str, name: str = "", price_cents: int = -1, description: str = "") -> str:
    """
    Update an existing Gumroad product listing.

    Args:
        product_id: The Gumroad product ID to update
        name: New product name (optional)
        price_cents: New price in cents (optional, pass -1 to skip)
        description: New product description (optional)

    Returns:
        Confirmation string with updated product details
    """
    try:
        params = {**_auth()}
        if name:
            params["name"] = name
        if price_cents >= 0:
            params["price"] = price_cents
        if description:
            params["description"] = description

        if len(params) == 1:
            return "Nothing to update — provide at least one of: name, price_cents, description."

        response = requests.put(f"{BASE_URL}/products/{product_id}", params=params)
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        p = data.get("product", {})
        price = f"${p.get('price', 0) / 100:.2f}"
        return f"Updated '{p.get('name')}' — Price: {price} — ID: {p.get('id')}"

    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def enable_product(product_id: str) -> str:
    """
    Publish a Gumroad product so it is live and purchasable.

    Args:
        product_id: The Gumroad product ID to publish

    Returns:
        Confirmation string
    """
    try:
        response = requests.put(f"{BASE_URL}/products/{product_id}/enable", params=_auth())
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        p = data.get("product", {})
        return f"'{p.get('name')}' is now live. URL: {p.get('short_url', '')}"

    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def disable_product(product_id: str) -> str:
    """
    Unpublish a Gumroad product so it is no longer purchasable.

    Args:
        product_id: The Gumroad product ID to unpublish

    Returns:
        Confirmation string
    """
    try:
        response = requests.put(f"{BASE_URL}/products/{product_id}/disable", params=_auth())
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        p = data.get("product", {})
        return f"'{p.get('name')}' has been unpublished."

    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_sales(product_id: str = "", after: str = "", before: str = "", max_results: int = 10) -> str:
    """
    Retrieve recent sales data from the Gumroad store.

    Args:
        product_id: Filter by a specific product ID (optional)
        after: Filter sales after this date in YYYY-MM-DD format (optional)
        before: Filter sales before this date in YYYY-MM-DD format (optional)
        max_results: Maximum number of sales to return (defaults to 10)

    Returns:
        A formatted string listing sales with buyer, product, amount, and date
    """
    try:
        params = {**_auth()}
        if product_id:
            params["product_id"] = product_id
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        response = requests.get(f"{BASE_URL}/sales", params=params)
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        sales = data.get("sales", [])[:max_results]
        if not sales:
            return "No sales found for the given filters."

        total = sum(s.get("price", 0) for s in sales)
        lines = [f"{len(sales)} sale(s) — Total: ${total / 100:.2f}\n"]

        for s in sales:
            amount = f"${s.get('price', 0) / 100:.2f}"
            lines.append(
                f"ID: {s.get('id')}\n"
                f"Product: {s.get('product_name', 'Unknown')}\n"
                f"Buyer: {s.get('email', 'Unknown')}\n"
                f"Amount: {amount}\n"
                f"Date: {s.get('created_at', 'Unknown')}"
            )

        return "\n---\n".join(lines)

    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_sale(sale_id: str) -> str:
    """
    Retrieve details for a single sale by its ID.

    Args:
        sale_id: The Gumroad sale ID

    Returns:
        A formatted string with full sale details
    """
    try:
        response = requests.get(f"{BASE_URL}/sales/{sale_id}", params=_auth())
        data = response.json()

        if not data.get("success"):
            return f"Gumroad error: {data.get('message', 'Unknown error')}"

        s = data.get("sale", {})
        amount = f"${s.get('price', 0) / 100:.2f}"

        return (
            f"Sale ID: {s.get('id')}\n"
            f"Product: {s.get('product_name', 'Unknown')}\n"
            f"Buyer: {s.get('email', 'Unknown')}\n"
            f"Amount: {amount}\n"
            f"Date: {s.get('created_at', 'Unknown')}\n"
            f"Refunded: {'Yes' if s.get('refunded') else 'No'}"
        )

    except Exception as e:
        return f"Unexpected error: {str(e)}"