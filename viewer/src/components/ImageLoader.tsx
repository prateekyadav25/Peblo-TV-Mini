import { useState } from "react";

export default function ImageLoader({
  src,
  alt,
  className,
}: {
  src: string;
  alt: string;
  className: string;
}) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  return (
    <div
      className={`relative ${className} bg-slate-800 animate-pulse overflow-hidden`}
    >
      {!failed && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 ${loaded ? "opacity-100" : "opacity-0"}`}
        />
      )}
      {failed && (
        <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400 bg-slate-800">
          Image unavailable
        </div>
      )}
    </div>
  );
}
