import { FaStar, FaBookOpen } from 'react-icons/fa';

export default function BookCard({ title, author, reason, summary, category, rating, image_url, index }) {
  return (
    <div 
      className="group relative bg-white/20 backdrop-blur-md rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 overflow-hidden border border-white/30 h-full flex flex-col transform hover:-translate-y-1"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Image Container - Adjusted aspect ratio for smaller cards */}
      <div className="relative aspect-[3/4] overflow-hidden bg-white/5">
        <img
          src={image_url}
          alt={title}
          className="w-full h-full object-cover transform group-hover:scale-110 transition-all duration-700"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        
        {/* Quick info badge */}
        <div className="absolute top-2 right-2 flex gap-1">
          <span className="px-2 py-1 bg-amber-900/80 backdrop-blur-md text-[10px] font-bold text-white rounded-lg shadow-sm border border-white/20">
            {category || 'General'}
          </span>
        </div>
      </div>

      {/* Content Area - More compact padding */}
      <div className="p-4 flex-grow flex flex-col">
        <div className="mb-2">
          <h3 className="font-black text-amber-950 text-sm line-clamp-2 group-hover:text-amber-800 transition-colors leading-tight">
            {title}
          </h3>
          <p className="text-xs text-amber-900/70 mt-1 truncate font-semibold">
            {author}
          </p>
        </div>

        {/* Rating and Meta */}
        <div className="mt-auto pt-3 flex items-center justify-between border-t border-amber-900/10">
          <div className="flex items-center gap-1.5">
            <div className="flex text-amber-600">
              {[...Array(5)].map((_, i) => (
                <FaStar key={i} className={`w-3 h-3 ${i < Math.floor(parseFloat(rating) || 4.5) ? 'fill-current' : 'text-amber-900/10'}`} />
              ))}
            </div>
            <span className="text-[10px] font-black text-amber-900/50">
              {(parseFloat(rating) || 4.5).toFixed(1)}
            </span>
          </div>
          
          <div className="flex items-center gap-1 text-amber-900/40 group-hover:text-amber-900/80 transition-colors">
            <FaBookOpen className="w-3 h-3" />
            <span className="text-[10px] font-bold">Details</span>
          </div>
        </div>
      </div>

      {/* Hover Action Button */}
      <div className="absolute bottom-3 right-3 translate-y-8 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300">
        <div className="p-2 bg-amber-800 text-white rounded-xl shadow-lg hover:bg-amber-900 transition-colors">
          <FaBookOpen className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}