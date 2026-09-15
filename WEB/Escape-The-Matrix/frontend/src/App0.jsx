import { useState } from 'react'
import './App.css'

function App() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async (e) => {
    e.preventDefault()
    
    if (!searchQuery.trim()) {
      setError('Please enter a search query')
      return
    }

    setIsLoading(true)
    setError('')
    
    try {
      const response = await fetch(`/search?q=${encodeURIComponent(searchQuery)}`)
      const result = await response.text()
      setSearchResults(result)
    } catch (err) {
      setError('Failed to connect to server. Make sure the backend is running on localhost:8080')
    } finally {
      setIsLoading(false)
    }
  }

  const clearResults = () => {
    setSearchResults('')
    setSearchQuery('')
    setError('')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>SandwishPicnic Search</h1>
        <p>Find your favorite sandwiches and picnic spots!</p>
      </header>

      <main className="search-container">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-container">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for sandwiches, ingredients, locations..."
              className="search-input"
            />
            <button 
              type="submit" 
              disabled={isLoading}
              className="search-button"
            >
              {isLoading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {searchResults && (
          <div className="results-container">
            <div className="results-header">
              <h3>Search Results:</h3>
              <button onClick={clearResults} className="clear-button">
                Clear
              </button>
            </div>
            <div className="results-content">
              {searchResults}
            </div>
          </div>
        )}

        {!searchResults && !error && !isLoading && (
          <div className="welcome-message">
            <h3>Welcome to SandwishPicnic! 🌭</h3>
            <p>Use the search bar above to find:</p>
            <ul>
              <li> Delicious sandwich recipes</li>
              <li> Perfect picnic locations</li>
              <li> Fresh ingredients and supplies</li>
              <li> Weather-perfect outdoor spots</li>
            </ul>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
