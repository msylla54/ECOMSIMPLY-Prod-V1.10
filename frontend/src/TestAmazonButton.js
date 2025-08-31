import React from 'react';
import AmazonConnectionManager from './components/AmazonConnectionManager';

/**
 * Test page pour valider le bouton Amazon
 * Permet de tester le composant sans authentification
 */
const TestAmazonButton = () => {
  // Mock user pour test
  const mockUser = {
    id: 'test-user-id',
    email: 'test@example.com',
    name: 'Test User',
    is_admin: true
  };

  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            🧪 Test Amazon Button Fix
          </h1>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-blue-900 mb-4">
              Test Instructions
            </h2>
            <ul className="list-disc list-inside space-y-2 text-blue-800">
              <li>Click on "Connecter mon compte Amazon" button below</li>
              <li>The modal should now open (fixed bug)</li>
              <li>You should see a demo Amazon authorization URL</li>
              <li>In production, configure real Amazon credentials</li>
            </ul>
          </div>

          {/* Amazon Connection Manager Component */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Amazon Connection Manager (Fixed)
            </h3>
            <AmazonConnectionManager user={mockUser} />
          </div>

          <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-900 mb-4">
              ✅ Bug Fix Applied
            </h3>
            <ul className="list-disc list-inside space-y-2 text-green-800">
              <li>Backend now returns demo response instead of crashing</li>
              <li>Frontend button should trigger modal opening</li>
              <li>OAuth flow works in demo mode</li>
              <li>Production requires real Amazon SP-API credentials</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestAmazonButton;