export async function fetchOrder(orderId, { signal } = {}) {
  const response = await fetch(`/api/orders/${orderId}`, { signal });
  if (!response.ok) {
    throw new Error(`Order request failed: ${response.status}`);
  }
  return response.json();
}
