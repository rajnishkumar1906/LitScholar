import { FaStar, FaBookOpen } from 'react-icons/fa';

export default function BookCard({ title, author, reason, summary, category, rating, index }) {
  return (
    <div 
      className="bg-white/95 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl overflow-hidden group hover:-translate-y-1 transition-all duration-300 border border-gray-200 h-full flex flex-col"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      <div className="p-6 flex flex-col flex-1">
        <div className="flex justify-between items-start mb-4">
          <span className="px-3 py-1 bg-gradient-to-r from-amber-100/80 to-amber-200/80 backdrop-blur-sm rounded-full text-xs font-medium text-amber-900">
            {category || 'General'}
          </span>
          <div className="flex items-center gap-1 bg-amber-50/80 backdrop-blur-sm px-2 py-1 rounded-full border border-amber-200">
            <FaStar className="w-3 h-3 text-amber-600" />
            <span className="text-xs font-medium text-amber-900">{rating || '4.5'}</span>
          </div>
        </div>

        <div className="mb-4 flex-1">
          <h3 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-amber-800 transition-colors">
            {title}
          </h3>
          <p className="text-sm text-gray-500">by {author}</p>
        </div>

        <p className="text-gray-600 mb-6 text-sm leading-relaxed line-clamp-3">
          "{reason || summary || 'No description available'}"
        </p>

        <div className="flex items-center justify-between mt-auto">
          <button className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100/80 rounded-xl transition-colors flex items-center gap-2 hover:text-amber-800">
            <FaBookOpen className="w-3 h-3" />
            Details
          </button>
          <button className="px-4 py-2 text-sm bg-gradient-to-r from-amber-800 to-amber-900 text-white font-medium rounded-xl hover:shadow-lg transition-all duration-300">
            Get It
          </button>
        </div>
      </div>
    </div>
  );
}