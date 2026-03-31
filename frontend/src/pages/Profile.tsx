import React, { useState, useEffect } from 'react';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

interface UserProfile {
    name: string;
    height_cm: string;
    weight_kg: string;
    age: string;
    activity_level: 'sedentary' | 'moderate' | 'active';
    goal: 'lose' | 'maintain' | 'gain';
    daily_target_kcal: number;
    bmi: number | null;
    daily_target_protein_g: number;
    daily_target_carbs_g: number;
    daily_target_fats_g: number;
}

const Profile: React.FC = () => {
    const [profile, setProfile] = useState<UserProfile>({
        name: 'Guest User',
        height_cm: '',
        weight_kg: '',
        age: '',
        activity_level: 'moderate',
        goal: 'maintain',
        daily_target_kcal: 2000,
        bmi: null,
        daily_target_protein_g: 150,
        daily_target_carbs_g: 200,
        daily_target_fats_g: 65,
    });
    const [saving, setSaving] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/v1/user/profile')
            .then((res) => res.json())
            .then((data) => {
                setProfile({
                    name: data.name || 'Guest User',
                    height_cm: data.height_cm ? String(data.height_cm) : '',
                    weight_kg: data.weight_kg ? String(data.weight_kg) : '',
                    age: data.age ? String(data.age) : '',
                    activity_level: data.activity_level || 'moderate',
                    goal: data.goal || 'maintain',
                    daily_target_kcal: data.daily_target_kcal || 2000,
                    bmi: data.bmi || null,
                    daily_target_protein_g: data.daily_target_protein_g || 150,
                    daily_target_carbs_g: data.daily_target_carbs_g || 200,
                    daily_target_fats_g: data.daily_target_fats_g || 65,
                });
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setProfile({ ...profile, [name]: value });
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const payload: Record<string, unknown> = {
                name: profile.name,
                activity_level: profile.activity_level,
                goal: profile.goal,
            };
            if (profile.height_cm) payload.height_cm = parseFloat(profile.height_cm);
            if (profile.weight_kg) payload.weight_kg = parseFloat(profile.weight_kg);
            if (profile.age) payload.age = parseInt(profile.age, 10);

            const res = await fetch('/api/v1/user/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json();
            setProfile({
                name: data.name,
                height_cm: data.height_cm ? String(data.height_cm) : '',
                weight_kg: data.weight_kg ? String(data.weight_kg) : '',
                age: data.age ? String(data.age) : '',
                activity_level: data.activity_level,
                goal: data.goal,
                daily_target_kcal: data.daily_target_kcal,
                bmi: data.bmi,
                daily_target_protein_g: data.daily_target_protein_g,
                daily_target_carbs_g: data.daily_target_carbs_g,
                daily_target_fats_g: data.daily_target_fats_g,
            });
        } catch (err) {
            console.error('Failed to save profile', err);
        }
        setSaving(false);
    };

    if (loading) {
        return (
            <div className="max-w-lg mx-auto text-center py-20">
                <p className="text-gray-400">Loading profile...</p>
            </div>
        );
    }

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
                                name="height_cm"
                                value={profile.height_cm}
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
                                name="weight_kg"
                                value={profile.weight_kg}
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
                            name="activity_level"
                            value={profile.activity_level}
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

                    {/* Daily Targets */}
                    <div className="pt-4 border-t border-white/10 space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Daily Calorie Target</span>
                            <span className="text-2xl font-bold text-emerald-400">
                                {profile.daily_target_kcal} kcal
                            </span>
                        </div>

                        {profile.bmi && (
                            <div className="flex justify-between items-center">
                                <span className="text-gray-400">BMI</span>
                                <span className="text-lg font-semibold text-blue-400">
                                    {profile.bmi}
                                </span>
                            </div>
                        )}

                        <div className="grid grid-cols-3 gap-3 pt-2">
                            <div className="bg-gray-700/30 rounded-lg p-3 text-center">
                                <p className="text-xs text-gray-500 mb-1">Protein</p>
                                <p className="text-sm font-bold text-emerald-400">
                                    {profile.daily_target_protein_g}g
                                </p>
                            </div>
                            <div className="bg-gray-700/30 rounded-lg p-3 text-center">
                                <p className="text-xs text-gray-500 mb-1">Carbs</p>
                                <p className="text-sm font-bold text-yellow-400">
                                    {profile.daily_target_carbs_g}g
                                </p>
                            </div>
                            <div className="bg-gray-700/30 rounded-lg p-3 text-center">
                                <p className="text-xs text-gray-500 mb-1">Fats</p>
                                <p className="text-sm font-bold text-rose-400">
                                    {profile.daily_target_fats_g}g
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Save Button */}
                    <Button onClick={handleSave} className="w-full" disabled={saving}>
                        {saving ? '⏳ Saving...' : '💾 Save Profile'}
                    </Button>
                </div>
            </Card>
        </div>
    );
};

export default Profile;
