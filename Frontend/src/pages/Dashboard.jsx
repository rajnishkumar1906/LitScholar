import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import ToggleButton from '../components/ToggleButton';
import RecommendationDashboard from '../components/RecommendationsDashboard';
import SearchQuery from '../components/SearchQuery';
import { useApp } from '../context/AppContext';

export default function Dashboard() {
  const navigate = useNavigate();
  const { trackBook } = useApp();
  const [showSearchSection, setShowSearchSection] = useState(false);
  const [isRotating, setIsRotating] = useState(false);

  const handleBookClick = (book) => {
    const id = book?.id || book?.book_id;
    if (!id) return;

    trackBook(id);
    navigate(`/book/${id}`, { state: { book } });
  };

  const handleToggle = () => {
    setIsRotating(true);
    setTimeout(() => {
      setShowSearchSection(!showSearchSection);
    }, 150);
    setTimeout(() => {
      setIsRotating(false);
    }, 600);
  };

  return (
    <div className="min-h-screen flex flex-col relative">
      <Navbar />

      <main className="flex-grow max-w-8xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {!showSearchSection ? (
          <RecommendationDashboard onBookClick={handleBookClick} />
        ) : (
          <SearchQuery onBookClick={handleBookClick} />
        )}
      </main>

      <ToggleButton
        showSearchSection={showSearchSection}
        onToggle={handleToggle}
        isRotating={isRotating}
      />

      <Footer />
    </div>
  );
}