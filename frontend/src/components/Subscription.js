import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { paymentAPI } from '../services/authAPI';

export default function Subscription() {
  const { tier, isPro } = useAuth();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const data = await paymentAPI.createCheckoutSession('PRO');
      window.location.href = data.url;
    } catch (err) {
      alert('Upgrade failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleManage = async () => {
    setLoading(true);
    try {
      const data = await paymentAPI.createPortalSession();
      window.location.href = data.url;
    } catch (err) {
      alert('Failed to open portal: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h2 className="text-3xl font-bold text-center mb-8">Subscription Plans</h2>

      <div className="grid md:grid-cols-2 gap-8">
        {/* BASIC Plan */}
        <div className={`bg-white rounded-sm shadow-lg p-8 ${!isPro ? 'ring-2 ring-blue-500' : ''}`}>
          <div className="text-center mb-6">
            <h3 className="text-2xl font-bold">BASIC</h3>
            <div className="text-4xl font-bold mt-2">FREE</div>
          </div>
          <ul className="space-y-3 mb-8">
            <li className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              5 simulations per hour
            </li>
            <li className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              Claude Sonnet 3.5 AI
            </li>
            <li className="flex items-center">
              <span className="text-green-500 mr-2">✓</span>
              Basic match analysis
            </li>
            <li className="flex items-center">
              <span className="text-gray-400 mr-2">✗</span>
              Sharp bookmaker insights
            </li>
          </ul>
          {!isPro && (
            <div className="text-center text-sm text-gray-600">Current Plan</div>
          )}
        </div>

        {/* PRO Plan */}
        <div className={`bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-sm shadow-2xl p-8 text-gray-900 ${isPro ? 'ring-4 ring-yellow-600' : ''}`}>
          <div className="text-center mb-6">
            <h3 className="text-2xl font-bold">PRO</h3>
            <div className="text-4xl font-bold mt-2">$19.99<span className="text-lg">/mo</span></div>
          </div>
          <ul className="space-y-3 mb-8">
            <li className="flex items-center">
              <span className="text-gray-900 mr-2">✓</span>
              Unlimited simulations
            </li>
            <li className="flex items-center">
              <span className="text-gray-900 mr-2">✓</span>
              Claude Sonnet 4.5 AI
            </li>
            <li className="flex items-center">
              <span className="text-gray-900 mr-2">✓</span>
              Advanced analysis
            </li>
            <li className="flex items-center">
              <span className="text-gray-900 mr-2">✓</span>
              Sharp bookmaker insights
            </li>
            <li className="flex items-center">
              <span className="text-gray-900 mr-2">✓</span>
              Extended context
            </li>
          </ul>
          {isPro ? (
            <button
              onClick={handleManage}
              disabled={loading}
              className="w-full bg-gray-900 text-white py-3 rounded-sm font-semibold hover:bg-gray-800 disabled:bg-gray-700"
            >
              {loading ? 'Loading...' : 'Manage Subscription'}
            </button>
          ) : (
            <button
              onClick={handleUpgrade}
              disabled={loading}
              className="w-full bg-gray-900 text-white py-3 rounded-sm font-semibold hover:bg-gray-800 disabled:bg-gray-700"
            >
              {loading ? 'Loading...' : 'Upgrade to PRO'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
