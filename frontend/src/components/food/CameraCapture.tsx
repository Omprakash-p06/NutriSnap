import React, { useState, useRef, useCallback } from 'react';
import Button from '../common/Button';
import { Camera, Upload, X } from 'lucide-react';

interface CameraCaptureProps {
    onCapture: (file: File | string) => void;
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture }) => {
    const [mode, setMode] = useState<'upload' | 'camera'>('upload');
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const startCamera = async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment' },
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
            setMode('camera');
            setError(null);
        } catch (err) {
            setError('Camera access denied. Please use file upload.');
        }
    };

    const stopCamera = useCallback(() => {
        if (stream) {
            stream.getTracks().forEach((track) => track.stop());
            setStream(null);
        }
        setMode('upload');
    }, [stream]);

    const capturePhoto = () => {
        if (!videoRef.current) return;

        const canvas = document.createElement('canvas');
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;

        const ctx = canvas.getContext('2d');
        if (ctx) {
            ctx.drawImage(videoRef.current, 0, 0);
            canvas.toBlob((blob) => {
                if (blob) {
                    const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
                    stopCamera();
                    onCapture(file);
                }
            }, 'image/jpeg', 0.9);
        }
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            onCapture(file);
        }
    };

    return (
        <div className="bg-gray-800/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
            {mode === 'upload' ? (
                <div className="space-y-4">
                    {/* Upload Area */}
                    <div
                        className="border-2 border-dashed border-white/20 rounded-xl p-8 text-center cursor-pointer hover:border-emerald-500/50 transition-colors group"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <div className="mb-4 text-gray-400 group-hover:text-emerald-400 transition-colors">
                            <Upload size={48} className="mx-auto" />
                        </div>
                        <p className="text-white font-medium">Click to upload image</p>
                        <p className="text-sm text-gray-400">or drag and drop</p>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            onChange={handleFileUpload}
                            className="hidden"
                        />
                    </div>

                    {/* Divider */}
                    <div className="flex items-center">
                        <div className="flex-1 border-t border-white/10"></div>
                        <span className="px-4 text-gray-500">or</span>
                        <div className="flex-1 border-t border-white/10"></div>
                    </div>

                    {/* Camera Button */}
                    <Button onClick={startCamera} variant="outline" className="w-full">
                        <Camera className="mr-2" size={20} />
                        Use Camera
                    </Button>

                    {error && (
                        <p className="text-red-400 text-sm text-center">{error}</p>
                    )}
                </div>
            ) : (
                <div className="space-y-4">
                    {/* Video Preview */}
                    <div className="relative rounded-xl overflow-hidden bg-black aspect-[4/3]">
                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full h-full object-cover"
                        />
                    </div>

                    {/* Controls */}
                    <div className="flex space-x-4">
                        <Button onClick={capturePhoto} className="flex-1">
                            <Camera className="mr-2" size={20} />
                            Capture
                        </Button>
                        <Button onClick={stopCamera} variant="outline">
                            <X className="mr-2" size={20} />
                            Cancel
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CameraCapture;
