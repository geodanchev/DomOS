import React, { useState, useEffect } from 'react';
import { apartmentsApi } from '../services/api';
import type { Apartment, ApartmentCreate, ApartmentUpdate } from '../types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { useToast } from '@/hooks/use-toast';
import { Plus, Pencil, Trash2, Building2, Loader2 } from 'lucide-react';

const Apartments: React.FC = () => {
  const [apartments, setApartments] = useState<Apartment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [editingApartment, setEditingApartment] = useState<Apartment | null>(null);
  const [deletingApartment, setDeletingApartment] = useState<Apartment | null>(null);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  // Form state
  const [formData, setFormData] = useState<ApartmentCreate>({
    number: '',
    floor: null,
    owner_name: '',
    residents_count: 0,
    monthly_fee: 0,
    notes: null,
  });

  const loadApartments = async () => {
    try {
      setLoading(true);
      const data = await apartmentsApi.getAll();
      setApartments(data.items);
    } catch (error) {
      toast({
        title: 'Грешка',
        description: 'Неуспешно зареждане на апартаменти',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApartments();
  }, []);

  const resetForm = () => {
    setFormData({
      number: '',
      floor: null,
      owner_name: '',
      residents_count: 0,
      monthly_fee: 0,
      notes: null,
    });
    setEditingApartment(null);
  };

  const openCreateDialog = () => {
    resetForm();
    setIsDialogOpen(true);
  };

  const openEditDialog = (apartment: Apartment) => {
    setEditingApartment(apartment);
    setFormData({
      number: apartment.number,
      floor: apartment.floor,
      owner_name: apartment.owner_name,
      residents_count: apartment.residents_count,
      monthly_fee: apartment.monthly_fee,
      notes: apartment.notes,
    });
    setIsDialogOpen(true);
  };

  const openDeleteDialog = (apartment: Apartment) => {
    setDeletingApartment(apartment);
    setIsDeleteDialogOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.number.trim()) {
      toast({
        title: 'Грешка',
        description: 'Номерът на апартамента е задължителен',
        variant: 'destructive',
      });
      return;
    }

    if (!formData.owner_name.trim()) {
      toast({
        title: 'Грешка',
        description: 'Името на собственика е задължително',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      
      if (editingApartment) {
        // Update existing
        const updateData: ApartmentUpdate = { ...formData };
        await apartmentsApi.update(editingApartment.id, updateData);
        toast({
          title: 'Успех',
          description: `Апартамент ${formData.number} е обновен`,
        });
      } else {
        // Create new
        await apartmentsApi.create(formData);
        toast({
          title: 'Успех',
          description: `Апартамент ${formData.number} е добавен`,
        });
      }
      
      setIsDialogOpen(false);
      resetForm();
      loadApartments();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Неуспешно запазване';
      toast({
        title: 'Грешка',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingApartment) return;
    
    try {
      await apartmentsApi.delete(deletingApartment.id);
      toast({
        title: 'Успех',
        description: `Апартамент ${deletingApartment.number} е изтрит`,
      });
      setIsDeleteDialogOpen(false);
      setDeletingApartment(null);
      loadApartments();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Неуспешно изтриване';
      toast({
        title: 'Грешка',
        description: message,
        variant: 'destructive',
      });
    }
  };

  const handleInputChange = (field: keyof ApartmentCreate, value: string | number | null) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Building2 className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-2xl font-bold">Домова книга</h1>
            <p className="text-muted-foreground">
              {apartments.length} апартамент{apartments.length !== 1 ? 'а' : ''}
            </p>
          </div>
        </div>
        <Button onClick={openCreateDialog} className="gap-2">
          <Plus className="h-4 w-4" />
          Добави апартамент
        </Button>
      </div>

      {/* Apartments Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-20">№</TableHead>
              <TableHead className="w-20">Етаж</TableHead>
              <TableHead>Собственик</TableHead>
              <TableHead className="w-24 text-center">Живущи</TableHead>
              <TableHead className="w-32 text-right">Месечна такса</TableHead>
              <TableHead>Бележки</TableHead>
              <TableHead className="w-24 text-right">Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {apartments.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                  Няма добавени апартаменти
                </TableCell>
              </TableRow>
            ) : (
              apartments.map((apartment) => (
                <TableRow key={apartment.id}>
                  <TableCell className="font-medium">{apartment.number}</TableCell>
                  <TableCell>
                    {apartment.floor !== null ? (
                      apartment.floor === 0 ? 'Партер' : 
                      apartment.floor < 0 ? `Сутерен ${Math.abs(apartment.floor)}` :
                      `Етаж ${apartment.floor}`
                    ) : '-'}
                  </TableCell>
                  <TableCell>{apartment.owner_name}</TableCell>
                  <TableCell className="text-center">{apartment.residents_count}</TableCell>
                  <TableCell className="text-right font-medium">
                    {apartment.monthly_fee.toFixed(2)} лв.
                  </TableCell>
                  <TableCell className="text-muted-foreground max-w-xs truncate">
                    {apartment.notes || '-'}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openEditDialog(apartment)}
                        title="Редактирай"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openDeleteDialog(apartment)}
                        className="text-destructive hover:text-destructive"
                        title="Изтрий"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              {editingApartment ? 'Редактиране на апартамент' : 'Добавяне на апартамент'}
            </DialogTitle>
            <DialogDescription>
              {editingApartment 
                ? 'Променете данните на апартамента' 
                : 'Въведете данните за новия апартамент'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="number">Номер на апартамент *</Label>
                  <Input
                    id="number"
                    value={formData.number}
                    onChange={(e) => handleInputChange('number', e.target.value)}
                    placeholder="напр. 1, 12А"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="floor">Етаж</Label>
                  <Input
                    id="floor"
                    type="number"
                    value={formData.floor ?? ''}
                    onChange={(e) => handleInputChange('floor', e.target.value ? parseInt(e.target.value) : null)}
                    placeholder="0 = партер"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="owner_name">Име на собственик *</Label>
                <Input
                  id="owner_name"
                  value={formData.owner_name}
                  onChange={(e) => handleInputChange('owner_name', e.target.value)}
                  placeholder="Иван Иванов"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="residents_count">Брой живущи</Label>
                  <Input
                    id="residents_count"
                    type="number"
                    min="0"
                    value={formData.residents_count}
                    onChange={(e) => {
                      const val = e.target.value;
                      handleInputChange('residents_count', val === '' ? 0 : parseInt(val));
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="monthly_fee">Месечна такса (лв.)</Label>
                  <Input
                    id="monthly_fee"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.monthly_fee}
                    onChange={(e) => handleInputChange('monthly_fee', parseFloat(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes">Бележки</Label>
                <Textarea
                  id="notes"
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value || null)}
                  placeholder="Допълнителна информация..."
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
              >
                Отказ
              </Button>
              <Button type="submit" disabled={saving}>
                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingApartment ? 'Запази' : 'Добави'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Изтриване на апартамент</AlertDialogTitle>
            <AlertDialogDescription>
              Сигурни ли сте, че искате да изтриете апартамент {deletingApartment?.number}?
              Това действие е необратимо и ще изтрие всички свързани плащания и задължения.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отказ</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Изтрий
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Apartments;