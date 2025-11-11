import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';

function MobileMenuButton({ onClick, isOpen }) {
  return (
    <button
      onClick={onClick}
      style={{
        position: 'fixed',
        top: '1rem',
        left: '1rem',
        zIndex: 1000,
        background: 'var(--primary-color)',
        color: 'white',
        border: 'none',
        borderRadius: '0.5rem',
        padding: '0.75rem',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        cursor: 'pointer',
        display: 'none'
      }}
      className="mobile-menu-btn"
    >
      {isOpen ? <X size={24} /> : <Menu size={24} />}
    </button>
  );
}

export default MobileMenuButton;

