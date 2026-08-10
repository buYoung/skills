import { lazy, Suspense, useEffect, useState } from 'react';
import { fetchOrder } from './orderApi.mjs';

export function OrderWorkspace({ orderId, onResolved }) {
  const OrderAuditPanel = lazy(() => import('./OrderAuditPanel.jsx'));
  const [order, setOrder] = useState(null);
  const [note, setNote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setIsLoading(true);
    setOrder(null);
    setError(null);

    fetchOrder(orderId)
      .then((nextOrder) => {
        setOrder(nextOrder);
        setNote(nextOrder.note ?? '');
        onResolved(nextOrder.id);
      })
      .catch(setError)
      .finally(() => setIsLoading(false));
  }, [orderId, onResolved]);

  if (isLoading) return <p>Loading order…</p>;
  if (error) return <p>Could not load order.</p>;
  if (!order) return null;

  return (
    <section>
      <h1>Order {order.id}</h1>
      <label>
        Internal note
        <textarea value={note} onChange={(event) => setNote(event.target.value)} />
      </label>
      <Suspense fallback={<p>Loading audit…</p>}>
        <OrderAuditPanel orderId={order.id} />
      </Suspense>
    </section>
  );
}
