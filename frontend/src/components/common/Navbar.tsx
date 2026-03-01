import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Camera, History, User } from 'lucide-react';

const navItems = [
    { path: '/', label: 'Home', icon: <Home size={20} /> },
    { path: '/scan', label: 'Scan', icon: <Camera size={20} /> },
    { path: '/history', label: 'History', icon: <History size={20} /> },
    { path: '/profile', label: 'Profile', icon: <User size={20} /> },
];

const Navbar: React.FC = () => {
    const location = useLocation();

    return (
        <nav className="sticky top-0 z-50 border-b border-white/10 bg-gray-900/80 backdrop-blur-md">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center space-x-2">
                        <span className="text-2xl">🥗</span>
                        <span className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                            NutriSnap
                        </span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center space-x-1">
                        {navItems.map((item) => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`
                                    px-4 py-2 rounded-lg font-medium transition-all duration-200 flex items-center space-x-2
                                    ${location.pathname === item.path
                                        ? 'bg-emerald-500/10 text-emerald-400'
                                        : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                    }
                                `}
                            >
                                {item.icon}
                                <span>{item.label}</span>
                            </Link>
                        ))}
                    </div>

                    {/* Mobile Navigation */}
                    <div className="md:hidden flex items-center space-x-6">
                        {navItems.map((item) => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`
                                    ${location.pathname === item.path
                                        ? 'text-emerald-400'
                                        : 'text-gray-500 hover:text-white'
                                    } transition-colors
                                `}
                            >
                                {item.icon}
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
