import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [identities, setIdentities] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [requests, setRequests] = useState([])
  const [activeTab, setActiveTab] = useState('directory') // directory, requests, audit

  // Form state
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    department: 'Engineering',
    job_title: 'Software Engineer',
    employee_id: ''
  })

  const [requestForm, setRequestForm] = useState({
    requester_id: '',
    entitlement: '',
    justification: ''
  })

  const [approverId, setApproverId] = useState('')

  const fetchIdentities = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/identities')
      const data = await res.json()
      setIdentities(data)
      // Set default approver if not set
      if (!approverId && data.length > 0) {
        setApproverId(data[0].id)
      }
    } catch (error) {
      console.error("Failed to fetch identities:", error)
    }
  }

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/audit/logs')
      const data = await res.json()
      setAuditLogs(data)
    } catch (error) {
      console.error("Failed to fetch logs:", error)
    }
  }

  const fetchRequests = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/requests')
      const data = await res.json()
      setRequests(data)
    } catch (error) {
      console.error("Failed to fetch requests:", error)
    }
  }

  useEffect(() => {
    fetchIdentities()
    fetchAuditLogs()
    fetchRequests()
    const interval = setInterval(() => {
      fetchIdentities()
      fetchAuditLogs()
      fetchRequests()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleRequestChange = (e) => {
    setRequestForm({ ...requestForm, [e.target.name]: e.target.value })
  }

  const triggerEvent = async (eventType, payload) => {
    setLoading(true)
    try {
      await fetch('http://localhost:8000/api/hr/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventType, ...payload })
      })
      fetchIdentities()
      fetchAuditLogs()
    } catch (error) {
      console.error(`Error triggering ${eventType}:`, error)
    } finally {
      setLoading(false)
    }
  }

  const submitAccessRequest = async (e) => {
    e.preventDefault()
    if (!requestForm.requester_id) {
      alert("Please select a requester")
      return
    }
    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestForm)
      })
      if (!res.ok) {
        const err = await res.json()
        alert(`Error: ${err.detail}`)
      } else {
        setRequestForm({ requester_id: '', entitlement: '', justification: '' })
        fetchRequests()
      }
    } catch (error) {
      console.error("Error submitting request:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleApproval = async (requestId, action) => {
    if (!approverId) {
      alert("Please select an approver first (top right of this tab)")
      return
    }
    try {
      const res = await fetch(`http://localhost:8000/api/requests/${requestId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approver_id: approverId })
      })
      if (!res.ok) {
        const err = await res.json()
        alert(`Error: ${err.detail}`)
      }
      fetchRequests()
      fetchIdentities() // To show new access
    } catch (error) {
      console.error(`Error ${action} request:`, error)
    }
  }

  const handleJoiner = (e) => {
    e.preventDefault()
    const payload = {
      employee_id: formData.employee_id || `EMP-${Math.floor(Math.random() * 10000)}`,
      first_name: formData.first_name,
      last_name: formData.last_name,
      email: formData.email,
      department: formData.department,
      job_title: formData.job_title
    }
    triggerEvent("EmployeeCreated", payload)
    // Reset form
    setFormData({
      first_name: '',
      last_name: '',
      email: '',
      department: 'Engineering',
      job_title: 'Software Engineer',
      employee_id: ''
    })
  }

  const handleMover = (identity) => {
    const newDept = prompt(`Enter new department for ${identity.first_name} (Engineering, Sales, Marketing, HR):`, "Sales")
    if (newDept) {
      triggerEvent("EmployeeUpdated", {
        employee_id: identity.employee_id,
        department: newDept
      })
    }
  }

  const handleLeaver = (identity) => {
    if (confirm(`Are you sure you want to terminate ${identity.first_name} ${identity.last_name}?`)) {
      triggerEvent("EmployeeTerminated", {
        employee_id: identity.employee_id
      })
    }
  }

  return (
    <div className="container">
      <header style={{ marginBottom: '2rem' }}>
        <h1>IGA Platform <span style={{ fontSize: '0.4em', color: '#94a3b8', verticalAlign: 'middle' }}>v1.1</span></h1>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
          <button onClick={() => setActiveTab('directory')} className={activeTab === 'directory' ? 'active' : ''}>Identity Directory</button>
          <button onClick={() => setActiveTab('requests')} className={activeTab === 'requests' ? 'active' : ''}>Access Requests</button>
          <button onClick={() => setActiveTab('audit')} className={activeTab === 'audit' ? 'active' : ''}>Audit Logs</button>
        </div>
      </header>

      {activeTab === 'directory' && (
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start', justifyContent: 'center' }}>

          {/* HR Simulation Panel */}
          <div className="card" style={{ minWidth: '300px' }}>
            <h2>HR Feed Simulator</h2>
            <form onSubmit={handleJoiner} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <input name="first_name" placeholder="First Name" value={formData.first_name} onChange={handleInputChange} required />
              <input name="last_name" placeholder="Last Name" value={formData.last_name} onChange={handleInputChange} required />
              <input name="email" placeholder="Email" value={formData.email} onChange={handleInputChange} required />
              <select name="department" value={formData.department} onChange={handleInputChange}>
                <option value="Engineering">Engineering</option>
                <option value="Sales">Sales</option>
                <option value="Marketing">Marketing</option>
                <option value="HR">HR</option>
              </select>
              <input name="job_title" placeholder="Job Title" value={formData.job_title} onChange={handleInputChange} />
              <button type="submit" disabled={loading}>
                {loading ? 'Processing...' : 'Trigger New Hire'}
              </button>
            </form>
          </div>

          {/* Identity Directory */}
          <div style={{ flex: 1 }}>
            <div className="grid">
              {identities.map(identity => (
                <div key={identity.id} className="card" style={{ opacity: identity.status === 'terminated' ? 0.6 : 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <h3 style={{ margin: 0 }}>{identity.first_name} {identity.last_name}</h3>
                    <span className={`status-badge status-${identity.status}`}>{identity.status}</span>
                  </div>
                  <p style={{ color: '#94a3b8', fontSize: '0.9em' }}>{identity.job_title} • {identity.department}</p>

                  <div style={{ marginTop: '1rem', fontSize: '0.85em' }}>
                    <strong>Entitlements:</strong>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                      {identity.entitlements.map(ent => (
                        <span key={ent} style={{ background: '#334155', padding: '2px 6px', borderRadius: '4px' }}>
                          {ent}
                        </span>
                      ))}
                    </div>
                  </div>

                  {identity.status === 'active' && (
                    <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.5rem' }}>
                      <button onClick={() => handleMover(identity)} style={{ fontSize: '0.8em', padding: '0.4em 0.8em', backgroundColor: '#f59e0b' }}>Move Dept</button>
                      <button onClick={() => handleLeaver(identity)} style={{ fontSize: '0.8em', padding: '0.4em 0.8em', backgroundColor: '#ef4444' }}>Terminate</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'requests' && (
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'flex-start', justifyContent: 'center' }}>

          {/* Request Form */}
          <div className="card" style={{ minWidth: '300px' }}>
            <h2>Request Access</h2>
            <form onSubmit={submitAccessRequest} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <label style={{ fontSize: '0.9em', color: '#94a3b8' }}>Request For:</label>
              <select name="requester_id" value={requestForm.requester_id} onChange={handleRequestChange} required>
                <option value="">Select Identity...</option>
                {identities.filter(i => i.status === 'active').map(i => (
                  <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
                ))}
              </select>

              <input name="entitlement" placeholder="Entitlement (e.g. GitHub:SuperAdmin)" value={requestForm.entitlement} onChange={handleRequestChange} required />
              <input name="justification" placeholder="Business Justification" value={requestForm.justification} onChange={handleRequestChange} required />

              <button type="submit" disabled={loading}>Submit Request</button>
            </form>
          </div>

          {/* Request List */}
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2>Access Requests</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.9em', color: '#94a3b8' }}>Act as Approver:</span>
                <select value={approverId} onChange={(e) => setApproverId(e.target.value)} style={{ padding: '0.3rem' }}>
                  {identities.filter(i => i.status === 'active').map(i => (
                    <option key={i.id} value={i.id}>{i.first_name} {i.last_name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid">
              {requests.map(req => {
                const requester = identities.find(i => i.id === req.requester_id)
                return (
                  <div key={req.id} className="card" style={{ borderLeft: `4px solid ${req.status === 'pending' ? '#fbbf24' : req.status === 'approved' ? '#10b981' : '#ef4444'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <h3 style={{ margin: 0, fontSize: '1.1em' }}>{req.entitlement}</h3>
                      <span style={{ fontSize: '0.8em', fontWeight: 'bold', textTransform: 'uppercase', color: req.status === 'pending' ? '#fbbf24' : req.status === 'approved' ? '#10b981' : '#ef4444' }}>{req.status}</span>
                    </div>
                    <p style={{ color: '#94a3b8', fontSize: '0.9em', margin: '0.5rem 0' }}>
                      For: <strong>{requester ? `${requester.first_name} ${requester.last_name}` : req.requester_id}</strong>
                    </p>
                    <p style={{ fontSize: '0.9em', fontStyle: 'italic', color: '#cbd5e1' }}>"{req.justification}"</p>

                    {req.status === 'pending' && (
                      <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                        <button onClick={() => handleApproval(req.id, 'approve')} style={{ fontSize: '0.8em', padding: '0.4em 0.8em', backgroundColor: '#10b981' }}>Approve</button>
                        <button onClick={() => handleApproval(req.id, 'reject')} style={{ fontSize: '0.8em', padding: '0.4em 0.8em', backgroundColor: '#ef4444' }}>Reject</button>
                      </div>
                    )}
                    {req.status !== 'pending' && (
                      <div style={{ marginTop: '0.5rem', fontSize: '0.8em', color: '#64748b' }}>
                        Decided by: {identities.find(i => i.id === req.approver_id)?.email || 'Unknown'}
                      </div>
                    )}
                  </div>
                )
              })}
              {requests.length === 0 && <div style={{ color: '#64748b' }}>No requests found.</div>}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
          <h2>System Audit Logs</h2>
          <div style={{ textAlign: 'left', maxHeight: '600px', overflowY: 'auto' }}>
            {auditLogs.map(log => (
              <div key={log.id} style={{ borderBottom: '1px solid #334155', padding: '1rem 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8em' }}>
                  <span>{new Date(log.timestamp).toLocaleString()}</span>
                  <span>{log.actor}</span>
                </div>
                <div style={{ marginTop: '0.25rem' }}>
                  <span style={{ color: '#38bdf8', fontWeight: 'bold' }}>{log.action}</span> on <span style={{ color: '#fff' }}>{log.target}</span>
                </div>
                <div style={{ fontSize: '0.8em', color: '#64748b', marginTop: '0.25rem' }}>
                  {JSON.stringify(log.details)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
