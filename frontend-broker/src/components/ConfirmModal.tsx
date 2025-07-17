import React, { useEffect, useRef } from 'react';
import { FaTimes } from 'react-icons/fa';
import './Dashboard.css';

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({ open, title, message, onConfirm, onCancel, loading }) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onCancel]);

  useEffect(() => {
    if (open && modalRef.current) {
      modalRef.current.focus();
    }
  }, [open]);

  if (!open) return null;
  return (
    <div className="modal-overlay" style={{backdropFilter:'blur(8px) saturate(1.2)', background:'rgba(30,34,45,0.18)'}}>
      <div
        className="modal confirm-modal"
        ref={modalRef}
        tabIndex={-1}
        style={{animation:'modalPop 0.28s cubic-bezier(.4,1.4,.6,1)'}}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
      >
        <button
          className="modal-close-btn"
          aria-label="Close"
          onClick={onCancel}
          style={{position:'absolute',top:18,right:18,background:'none',border:'none',fontSize:20,cursor:'pointer',color:'#888'}}
        >
          <FaTimes />
        </button>
        <h3 id="confirm-modal-title" style={{marginTop:0,marginBottom:16,fontWeight:700,fontSize:'1.2rem',color:'#1a2233'}}>{title}</h3>
        <div style={{marginBottom:24, color:'#222', fontSize:'1.05rem'}}>{message}</div>
        <div style={{display:'flex',justifyContent:'flex-end',gap:14}}>
          <button
            className="action-btn"
            style={{background:'#888'}}
            onClick={onCancel}
            disabled={loading}
          >Cancel</button>
          <button
            className="action-btn"
            style={{background:'#b71c1c',minWidth:90}}
            onClick={onConfirm}
            disabled={loading}
          >{loading ? 'Deleting...' : 'Delete'}</button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal; 