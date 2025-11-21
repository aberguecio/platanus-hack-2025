'use client'

import { useState, useEffect } from 'react'

interface Item {
  id: number
  title: string
  description: string
  completed: boolean
  created_at: string
}

export default function Home() {
  const [items, setItems] = useState<Item[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)

  const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

  useEffect(() => {
    fetchItems()
  }, [])

  const fetchItems = async () => {
    try {
      const response = await fetch(`${API_URL}/items/`)
      const data = await response.json()
      setItems(data)
    } catch (error) {
      console.error('Error fetching items:', error)
    }
  }

  const createItem = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/items/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, completed: false }),
      })
      if (response.ok) {
        setTitle('')
        setDescription('')
        fetchItems()
      }
    } catch (error) {
      console.error('Error creating item:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleComplete = async (id: number, completed: boolean) => {
    try {
      await fetch(`${API_URL}/items/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed: !completed }),
      })
      fetchItems()
    } catch (error) {
      console.error('Error updating item:', error)
    }
  }

  const deleteItem = async (id: number) => {
    try {
      await fetch(`${API_URL}/items/${id}`, { method: 'DELETE' })
      fetchItems()
    } catch (error) {
      console.error('Error deleting item:', error)
    }
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ textAlign: 'center', color: '#333' }}>📝 Simple Todo App</h1>

      <div style={{ backgroundColor: '#f5f5f5', padding: '20px', borderRadius: '8px', marginBottom: '30px' }}>
        <h2>Add New Item</h2>
        <form onSubmit={createItem}>
          <input
            type="text"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '4px', border: '1px solid #ddd' }}
          />
          <textarea
            placeholder="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '4px', border: '1px solid #ddd', minHeight: '80px' }}
          />
          <button
            type="submit"
            disabled={loading}
            style={{ width: '100%', padding: '12px', backgroundColor: '#0070f3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '16px' }}
          >
            {loading ? 'Creating...' : 'Create Item'}
          </button>
        </form>
      </div>

      <div>
        <h2>Items ({items.length})</h2>
        {items.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#666' }}>No items yet. Create one above!</p>
        ) : (
          <div>
            {items.map((item) => (
              <div
                key={item.id}
                style={{
                  backgroundColor: 'white',
                  padding: '15px',
                  marginBottom: '10px',
                  borderRadius: '8px',
                  border: '1px solid #ddd',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ flex: 1 }}>
                  <h3 style={{
                    margin: '0 0 5px 0',
                    textDecoration: item.completed ? 'line-through' : 'none',
                    color: item.completed ? '#999' : '#333'
                  }}>
                    {item.title}
                  </h3>
                  {item.description && (
                    <p style={{ margin: '0', color: '#666', fontSize: '14px' }}>{item.description}</p>
                  )}
                  <small style={{ color: '#999' }}>
                    Created: {new Date(item.created_at).toLocaleString()}
                  </small>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => toggleComplete(item.id, item.completed)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: item.completed ? '#28a745' : '#ffc107',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    {item.completed ? '✓' : '○'}
                  </button>
                  <button
                    onClick={() => deleteItem(item.id)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
