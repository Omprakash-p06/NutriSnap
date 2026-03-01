import React, { useState } from 'react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

interface UserProfile {
    name: string;
    height: string;
    weight: string;
    age: string;
    activityLevel: 'sedentary' | 'moderate' | 'active';
    goal: 'lose' | 'maintain' | 'gain';
    dailyTarget: number;
}

const Profile: React.FC = () => {
    const [profile, setProfile] = useState<UserProfile>({
        name: 'Guest User',
        height: '',
        weight: '',
        age: '',
        activityLevel: 'moderate',
        goal: 'maintain',
        dailyTarget: 2000,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setProfile({ ...profile, [name]: value });
    };

    const handleSave = () => {
        // Calculate TDEE if all values present
        if (profile.height && profile.weight && profile.age) {
            // Simplified TDEE calculation
            const weight = parseFloat(profile.weight);
            const height = parseFloat(profile.height);
            const age = parseFloat(profile.age);

            const bmr = 10 * weight + 6.25 * height - 5 * age + 5;
            const multipliers = { sedentary: 1.2, moderate: 1.55, active: 1.725 };
            const tdee = bmr * multipliers[profile.activityLevel];

            let target = tdee;
            if (profile.goal === 'lose') target -= 500;
            if (profile.goal === 'gain') target += 300;

            const newTarget = Math.round(target);
            setProfile({ ...profile, dailyTarget: newTarget });

            // In a real app, save to backend here
            // await updateProfile(profile);
        }
        alert('Profile saved!');
    };

    return (
        <div className="max-w-lg mx-auto space-y-6 pb-20 md:pb-0">
            {/* Header */}
            <div className="text-center">
                <h1 className="text-3xl font-bold text-white mb-2">Profile</h1>
                <p className="text-gray-400">Manage your nutrition goals</p>
            </div>

            {/* Profile Form */}
            <Card>
                <div className="space-y-4">
                    {/* Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">
                            Name
                        </label>
                        <input
                            type="text"
                            name="name"
                            value={profile.name}
                            onChange={handleChange}
                            className="w-full bg-gray-700/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                            placeholder="Your name"
                        />
                    </div>

                    {/* Height & Weight */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">
                                Height (cm)
                            </label>
                            <input
                                type="number"
                                name="height"
                                value={profile.height}
                                onChange={handleChange}
                                className="w-full bg-gray-700/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                                placeholder="170"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1">
                                Weight (kg)
                            </label>
                            <input
                                type="number"
                                name="weight"
                                value={profile.weight}
                                onChange={handleChange}
                                className="w-full bg-gray-700/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                                placeholder="70"
                            />
                        </div>
                    </div>

                    {/* Age */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">
                            Age
                        </label>
                        <input
                            type="number"
                            name="age"
                            value={profile.age}
                            onChange={handleChange}
                            className="w-full bg-gray-700/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                            placeholder="25"
                        />
                    </div>

                    {/* Activity Level */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">
                            Activity Level
                        </label>
                        <select
                            name="activityLevel"
                            value={profile.activityLevel}
                            onChange={handleChange}
                            className="w-full bg-gray-700/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                        >
                            <option value="sedentary">Sedentary (little/no exercise)</option>
                            <option value="moderate">Moderate (3-5 days/week)</option>
                            <option value="active">Active (6-7 days/week)</option>
                        </select>
                    </div>

                    {/* Goal */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">
                            Goal
                        </label>
                        <select
                            name="goal"
                            value={profile.goal}
                            onChange={handleChange}
                            className="w-full bg-gray-700/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-emerald-500 transition-colors"
                        >
                            <option value="lose">Lose Weight</option>
                            <option value="maintain">Maintain Weight</option>
                            <option value="gain">Gain Weight</option>
                        </select>
                    </div>

                    {/* Daily Target */}
                    <div className="pt-4 border-t border-white/10">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Daily Calorie Target</span>
                            <span className="text-2xl font-bold text-emerald-400">
                                {profile.dailyTarget} kcal
                            </span>
                        </div>
                    </div>

                    {/* Save Button */}
                    <Button onClick={handleSave} className="w-full">
                        💾 Save Profile
                    </Button>
                </div>
            </Card>
        </div>
    );
};

export default Profile;
