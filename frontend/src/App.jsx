import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Navbar from './components/Navbar'
import Footer from './components/Footer'

import Home from './pages/Home'
import Trajeto from './pages/Trajeto'
import Pesquisa from './pages/Pesquisa'
import Sobre from './pages/Sobre'

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/trajeto" element={<Trajeto />} />
        <Route path="/pesquisa" element={<Pesquisa />} />
        <Route path="/sobre" element={<Sobre />} />
      </Routes>

      <Footer />
    </BrowserRouter>
  )
}

export default App
