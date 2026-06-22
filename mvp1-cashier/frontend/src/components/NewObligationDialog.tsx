import React, { useState, useEffect } from 'react';
import { obligationsApi, apartmentsApi } from '../services/api';
import type { Apartment, ObligationType } from '../types';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface NewObligationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const OBLIGATION_TYPES: { value: ObligationType; label: string }[] = [
  { value: 'monthly', label: '📅 Месечна такса' },
  { value: 'initial', label: '🏠 Първоначална вноска' },
  { value: 'penalty', label: '⚠️ Санкция/Глоба' },
  { value: 'repair', label: '🔧 Ремонт' },
  { value: 'fund', label: '💰 Фонд' },
  { value: 'other', label: '📋 Друго' },
];

const NewObligationDialog: React.FC<NewObligationDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { toast } = useToast();
  const [apartments, setApartments] = useState<Apartment[]>([]);
  const [selectedApartmentId, setSelectedApartmentId] = useState<string>('');
  const [obligationType, setObligationType] = useState<ObligationType>('monthly');
  const [month, setMonth] = useState<string>('');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [isLoadingApartments, setIsLoadingApartments] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Set default month to current month
  useEffect(() => {
    const now = new Date();
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    setMonth(currentMonth);
  }, []);

  // Load apartments on open
  useEffect(() => {
    if (isOpen) {
      loadApartments();
    }
  }, [isOpen]);

  const loadApartments = async () => {
    try {
      setIsLoadingApartments(true);
      const data = await apartmentsApi.getAll();
      setApartments(data.items);
    } catch (err) {
      setError('Грешка при зареждане на апартаментите');
    } finally {
      setIsLoadingApartments(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApartmentId || selectedApartmentId === 'placeholder' || !amount) {
      setError('Моля изберете апартамент и въведете сума');
      return;
    }

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Моля въведете валидна сума');
      return;
    }

    // Validate month for monthly type
    if (obligationType === 'monthly' && !month) {
      setError('Моля изберете месец за месечната такса');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');

      await obligationsApi.create({
        type: obligationType,
        apartment_id: parseInt(selectedApartmentId),
        month: obligationType === 'monthly' ? month : null,
        amount: parsedAmount,
        description: description || null,
      });

      const selectedApt = apartments.find(a => a.id === parseInt(selectedApartmentId));
      const typeLabel = OBLIGATION_TYPES.find(t => t.value === obligationType)?.label || obligationType;

      toast({
        title: '✅ Задължението е добавено',
        description: `Ап. ${selectedApt?.number} - ${typeLabel} - ${parsedAmount.toFixed(2)} лв`,
        variant: 'success',
      });
      onSuccess();
      handleClose();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Грешка при запис на задължението';
      setError(errorMessage);
      toast({
        title: '❌ Грешка',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setSelectedApartmentId('');
    setObligationType('monthly');
    setAmount('');
    setDescription('');
    setError('');
    // Reset month to current
    const now = new Date();
    setMonth(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`);
    onClose();
  };

  // Generate month options (current month + next 11 months)
  const getMonthOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = -2; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
      const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      const monthNames = [
        'Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни',
        'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'
      ];
      const label = `${monthNames[d.getMonth()]} ${d.getFullYear()}`;
      options.push({ value, label });
    }
    return options;
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>📝 Ново задължение</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Error message */}
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-2 rounded-md text-sm">
              {error}
            </div>
          )}

          {/* Apartment selection */}
          <div className="space-y-2">
            <Label htmlFor="apartment">Апартамент *</Label>
            {isLoadingApartments ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Зареждане...
              </div>
            ) : (
              <Select
                value={selectedApartmentId}
                onValueChange={setSelectedApartmentId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Изберете апартамент" />
                </SelectTrigger>
                <SelectContent>
                  {apartments.map((apt) => (
                    <SelectItem key={apt.id} value={String(apt.id)}>
                      Ап. {apt.number} - {apt.owner_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Obligation type */}
          <div className="space-y-2">
            <Label htmlFor="type">Тип задължение *</Label>
            <Select
              value={obligationType}
              onValueChange={(value) => setObligationType(value as ObligationType)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {OBLIGATION_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Month selection (only for monthly type) */}
          {obligationType === 'monthly' && (
            <div className="space-y-2">
              <Label htmlFor="month">Месец *</Label>
              <Select value={month} onValueChange={setMonth}>
                <SelectTrigger>
                  <SelectValue placeholder="Изберете месец" />
                </SelectTrigger>
                <SelectContent>
                  {getMonthOptions().map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Amount */}
          <div className="space-y-2">
            <Label htmlFor="amount">Сума (лв) *</Label>
            <Input
              id="amount"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Описание (опционално)</Label>
            <Textarea
              id="description"
              placeholder="Допълнителна информация за задължението..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Отказ
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Запазване...
                </>
              ) : (
                '💾 Запази'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default NewObligationDialog;
