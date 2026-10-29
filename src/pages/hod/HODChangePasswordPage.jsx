import React from 'react';
import ChangePasswordCard from '../../components/common/ChangePasswordCard';

export default function HODChangePasswordPage() {
  return (
    <>
      <div className="teacher-content-header" style={{ marginBottom: '1.75rem' }}>
        <h2>Change Password</h2>
        <p>Update your account password securely.</p>
      </div>

      <ChangePasswordCard />
    </>
  );
}
