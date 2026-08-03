import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { usersApi } from '../services/api';
import type { UserProfileUpdate } from '../types';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { User as UserIcon, Mail, Phone, Lock, Camera, Loader2, Check, AlertCircle, Trash2, KeyRound, AtSign } from 'lucide-react';

export default function Settings() {
  const { user, setUser } = useAuth();
  const [displayName, setDisplayName] = useState(user?.display_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [usernamePassword, setUsernamePassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || '');
      setEmail(user.email || '');
      setPhone(user.phone || '');
    }
  }, [user]);

  const showMessage = (type: 'success' | 'error', message: string) => {
    type === 'success' ? (setSuccess(message), setError(null)) : (setError(message), setSuccess(null));
    setTimeout(() => { setSuccess(null); setError(null); }, 5000);
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const updateData: UserProfileUpdate = {};
      if (displayName !== user?.display_name) updateData.display_name = displayName;
      if (email !== (user?.email || '')) updateData.email = email || null;
      if (phone !== (user?.phone || '')) updateData.phone = phone || null;
      if (Object.keys(updateData).length === 0) { showMessage('error', 'Няма промени'); setLoading(false); return; }
      const updatedUser = await usersApi.updateProfile(updateData);
      setUser(updatedUser);
      showMessage('success', 'Профилът е обновен успешно');
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Грешка при обновяване');
    } finally { setLoading(false); }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) { showMessage('error', 'Паролите не съвпадат'); return; }
    if (newPassword.length < 4) { showMessage('error', 'Паролата трябва да е поне 4 символа'); return; }
    setLoading(true);
    try {
      await usersApi.changePassword({ current_password: currentPassword, new_password: newPassword, confirm_password: confirmPassword });
      setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
      showMessage('success', 'Паролата е сменена успешно');
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Грешка при смяна на паролата');
    } finally { setLoading(false); }
  };

  const handleUsernameChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newUsername.length < 3) { showMessage('error', 'Потребителското име трябва да е поне 3 символа'); return; }
    setLoading(true);
    try {
      const updatedUser = await usersApi.changeUsername({ new_username: newUsername, password: usernamePassword });
      setUser(updatedUser); setNewUsername(''); setUsernamePassword('');
      showMessage('success', 'Потребителското име е сменено успешно');
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Грешка при смяна на потребителското име');
    } finally { setLoading(false); }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) { showMessage('error', 'Невалиден формат'); return; }
    if (file.size > 5 * 1024 * 1024) { showMessage('error', 'Файлът е твърде голям'); return; }
    setAvatarUploading(true);
    try {
      const updatedUser = await usersApi.uploadAvatar(file);
      setUser(updatedUser);
      showMessage('success', 'Снимката е качена успешно');
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Грешка при качване');
    } finally { setAvatarUploading(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const handleAvatarDelete = async () => {
    if (!user?.avatar_url) return;
    setAvatarUploading(true);
    try {
      const updatedUser = await usersApi.deleteAvatar();
      setUser(updatedUser);
      showMessage('success', 'Снимката е премахната');
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Грешка при премахване');
    } finally { setAvatarUploading(false); }
  };

  const getInitials = (name: string) => name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  const getRoleDisplay = (role: string) => ({ admin: 'Администратор', cashier: 'Касиер', viewer: 'Само преглед' }[role] || role);

  if (!user) return null;

  return (
    <div className="container mx-auto py-6 px-4 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Настройки на профила</h1>
      {success && <Alert className="mb-4 border-green-500 bg-green-50"><Check className="h-4 w-4 text-green-600" /><AlertDescription className="text-green-600">{success}</AlertDescription></Alert>}
      {error && <Alert className="mb-4" variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert>}
      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="profile">Профил</TabsTrigger>
          <TabsTrigger value="security">Сигурност</TabsTrigger>
          <TabsTrigger value="account">Акаунт</TabsTrigger>
        </TabsList>
        <TabsContent value="profile">
          <div className="grid gap-6">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Camera className="h-5 w-5" />Профилна снимка</CardTitle><CardDescription>Качете снимка. Максимум 5MB.</CardDescription></CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <Avatar className="h-24 w-24"><AvatarImage src={user.avatar_url || undefined} alt={user.display_name} /><AvatarFallback className="text-2xl">{getInitials(user.display_name)}</AvatarFallback></Avatar>
                  <div className="flex flex-col gap-2">
                    <input ref={fileInputRef} type="file" accept="image/*" onChange={handleAvatarUpload} className="hidden" />
                    <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={avatarUploading}>
                      {avatarUploading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Качване...</> : <><Camera className="mr-2 h-4 w-4" />Качи снимка</>}
                    </Button>
                    {user.avatar_url && <Button variant="ghost" size="sm" className="text-red-600" onClick={handleAvatarDelete} disabled={avatarUploading}><Trash2 className="mr-2 h-4 w-4" />Премахни</Button>}
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><UserIcon className="h-5 w-5" />Лична информация</CardTitle></CardHeader>
              <CardContent>
                <form onSubmit={handleProfileUpdate} className="space-y-4">
                  <div className="grid gap-2"><Label htmlFor="display_name">Име за показване</Label><Input id="display_name" value={displayName} onChange={e => setDisplayName(e.target.value)} required /></div>
                  <div className="grid gap-2"><Label htmlFor="email" className="flex items-center gap-2"><Mail className="h-4 w-4" />Email</Label><Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com" /></div>
                  <div className="grid gap-2"><Label htmlFor="phone" className="flex items-center gap-2"><Phone className="h-4 w-4" />Телефон</Label><Input id="phone" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+359..." /></div>
                  <div className="pt-2"><Button type="submit" disabled={loading}>{loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Запазване...</> : 'Запази промените'}</Button></div>
                </form>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        <TabsContent value="security">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Lock className="h-5 w-5" />Смяна на парола</CardTitle><CardDescription>Сменете паролата си за по-добра сигурност.</CardDescription></CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordChange} className="space-y-4">
                <div className="grid gap-2"><Label htmlFor="current_password">Текуща парола</Label><Input id="current_password" type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required /></div>
                <div className="grid gap-2"><Label htmlFor="new_password">Нова парола</Label><Input id="new_password" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required /></div>
                <div className="grid gap-2"><Label htmlFor="confirm_password">Потвърдете новата парола</Label><Input id="confirm_password" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required /></div>
                <div className="pt-2"><Button type="submit" disabled={loading}>{loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Смяна...</> : <><KeyRound className="mr-2 h-4 w-4" />Смени паролата</>}</Button></div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="account">
          <div className="grid gap-6">
            <Card>
              <CardHeader><CardTitle>Информация за акаунта</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between"><span className="text-muted-foreground">Потребителско име:</span><span className="font-medium">{user.username}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Роля:</span><span className="font-medium">{getRoleDisplay(user.role)}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Създаден на:</span><span className="font-medium">{new Date(user.created_at).toLocaleDateString('bg-BG')}</span></div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><AtSign className="h-5 w-5" />Смяна на потребителско име</CardTitle><CardDescription>Изисква парола за потвърждение.</CardDescription></CardHeader>
              <CardContent>
                <form onSubmit={handleUsernameChange} className="space-y-4">
                  <div className="grid gap-2"><Label htmlFor="new_username">Ново потребителско име</Label><Input id="new_username" value={newUsername} onChange={e => setNewUsername(e.target.value)} required /></div>
                  <div className="grid gap-2"><Label htmlFor="username_password">Парола за потвърждение</Label><Input id="username_password" type="password" value={usernamePassword} onChange={e => setUsernamePassword(e.target.value)} required /></div>
                  <div className="pt-2"><Button type="submit" disabled={loading}>{loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Смяна...</> : <><AtSign className="mr-2 h-4 w-4" />Смени потребителското име</>}</Button></div>
                </form>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}