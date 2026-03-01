import React from 'react';

type LoaderSize = 'sm' | 'md' | 'lg';

interface LoaderProps {
    size?: LoaderSize;
    className?: string;
}

interface LoadingOverlayProps {
    message?: string;
}

const sizes: Record<LoaderSize, string> = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
};

const Loader: React.FC<LoaderProps> & {
    Overlay: React.FC<LoadingOverlayProps>;
} = ({ size = 'md', className = '' }) => {
    return (
        <div className={`flex items-center justify-center ${className}`}>
            <div
                className={`
                    ${sizes[size]}
                    border-4 border-emerald-500/30 border-t-emerald-500
                    rounded-full animate-spin
                `}
            />
        </div>
    );
};

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message = 'Loading...' }) => {
    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-gray-800 p-8 rounded-2xl shadow-xl text-center border border-white/10">
                <Loader size="lg" className="mb-4" />
                <p className="text-gray-300">{message}</p>
            </div>
        </div>
    );
};

Loader.Overlay = LoadingOverlay;

export default Loader;
