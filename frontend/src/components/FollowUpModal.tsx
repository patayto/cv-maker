import { useState, useEffect } from 'react';
import type { Job, ContactHistory, FollowUpMessage } from '../types/job';
import { contactApi } from '../services/api';

interface FollowUpModalProps {
  job: Job;
  onClose: () => void;
  onContactRecorded: () => void;
}

export function FollowUpModal({ job, onClose, onContactRecorded }: FollowUpModalProps) {
  const [messageType, setMessageType] = useState<'email' | 'linkedin'>('email');
  const [message, setMessage] = useState('');
  const [subject, setSubject] = useState('');
  const [loading, setLoading] = useState(false);
  const [contactHistory, setContactHistory] = useState<ContactHistory[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Load generated message and history
  useEffect(() => {
    loadMessage();
    loadHistory();
  }, [messageType]);

  const loadMessage = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await contactApi.generateFollowUp(job.id, messageType);
      setMessage(response.message);
      setSubject(response.subject || '');
    } catch (err) {
      setError('Failed to generate message');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await contactApi.getHistory(job.id);
      setContactHistory(response);
    } catch (err) {
      console.error('Failed to load contact history:', err);
    }
  };

  const handleCopyAndOpen = async () => {
    try {
      // Copy message to clipboard
      await navigator.clipboard.writeText(message);

      // Record the contact
      await contactApi.recordContact(job.id, {
        contact_method: messageType,
        message_content: message
      });

      // Open appropriate platform
      if (messageType === 'email' && job.recruiter_email) {
        const mailtoUrl = `mailto:${job.recruiter_email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(message)}`;
        window.open(mailtoUrl, '_blank');
      } else if (messageType === 'linkedin' && job.recruiter_linkedin) {
        window.open(job.recruiter_linkedin, '_blank');
      }

      // Notify parent and close
      onContactRecorded();
    } catch (err) {
      setError('Failed to record contact');
      console.error(err);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">Follow Up - {job.role}</h2>
            <p className="text-sm text-gray-600">{job.company}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Message Type Selector */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message Type
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setMessageType('email')}
                className={`px-4 py-2 rounded ${
                  messageType === 'email'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Email {job.recruiter_email ? '📧' : '(no email)'}
              </button>
              <button
                onClick={() => setMessageType('linkedin')}
                className={`px-4 py-2 rounded ${
                  messageType === 'linkedin'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                LinkedIn {job.recruiter_linkedin ? '🔗' : '(no profile)'}
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Recipient Info */}
          <div className="mb-4 p-3 bg-gray-50 rounded">
            <p className="text-sm text-gray-600">
              <strong>To:</strong> {job.recruiter_name || 'Hiring Manager'}
              {messageType === 'email' && job.recruiter_email && (
                <span className="ml-2">({job.recruiter_email})</span>
              )}
              {messageType === 'linkedin' && job.recruiter_linkedin && (
                <a
                  href={job.recruiter_linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-blue-600 hover:underline"
                >
                  View Profile →
                </a>
              )}
            </p>
          </div>

          {/* Subject Line (Email only) */}
          {messageType === 'email' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {/* Message Editor */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={12}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            />
          </div>

          {/* Contact History */}
          {contactHistory.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Contact History ({contactHistory.length})
              </h3>
              <div className="space-y-2">
                {contactHistory.map((contact) => (
                  <div
                    key={contact.id}
                    className="p-3 bg-gray-50 rounded text-sm"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium capitalize">
                        {contact.contact_method}
                      </span>
                      <span className="text-gray-500">
                        {formatDate(contact.contacted_at)}
                      </span>
                    </div>
                    {contact.notes && (
                      <p className="text-gray-600 text-xs">{contact.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4 flex items-center justify-between bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded"
          >
            Cancel
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => navigator.clipboard.writeText(message)}
              className="px-4 py-2 bg-gray-200 text-gray-700 hover:bg-gray-300 rounded"
            >
              Copy to Clipboard
            </button>
            <button
              onClick={handleCopyAndOpen}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : `Copy & Open ${messageType === 'email' ? 'Email' : 'LinkedIn'}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
