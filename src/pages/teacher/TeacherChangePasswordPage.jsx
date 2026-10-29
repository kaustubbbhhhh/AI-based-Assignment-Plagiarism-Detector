import React from 'react';
import ChangePasswordCard from '../../components/common/ChangePasswordCard';

export default function TeacherChangePasswordPage() {
  return (
    <>
      <div className="teacher-content-header">
        <h2>Change Password</h2>
        <p>Update your account password securely.</p>
      </div>

      <ChangePasswordCard />
    </>
  );
}
