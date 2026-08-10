// SENTINEL: react-owner-controlled-do-not-edit
import { memo } from 'react';

export const Dashboard = memo(function Dashboard({ metrics }) {
  'use memo';
  return <output>{metrics.join(', ')}</output>;
});
