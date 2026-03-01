import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    hover?: boolean;
}

const Card: React.FC<CardProps> & {
    Header: React.FC<React.HTMLAttributes<HTMLDivElement>>;
    Title: React.FC<React.HTMLAttributes<HTMLHeadingElement>>;
    Content: React.FC<React.HTMLAttributes<HTMLDivElement>>;
} = ({ children, hover = false, className = '', ...props }) => {
    return (
        <div
            className={`
                bg-gray-800/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6
                ${hover ? 'hover:bg-gray-800/70 hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300' : ''}
                ${className}
            `}
            {...props}
        >
            {children}
        </div>
    );
};

const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => {
    return (
        <div className={`mb-4 ${className}`} {...props}>
            {children}
        </div>
    );
};

const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ children, className = '', ...props }) => {
    return (
        <h3 className={`text-lg font-semibold text-white ${className}`} {...props}>
            {children}
        </h3>
    );
};

const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => {
    return (
        <div className={className} {...props}>
            {children}
        </div>
    );
};

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Content = CardContent;

export default Card;
