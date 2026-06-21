import React, { useState, useEffect } from 'react';
import { paymentsApi, apartmentsApi } from '../services/api';
import type { Apartment, ApartmentPaymentSummary, RecentPayment } from '../types';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface NewPaymentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const NewPaymentDialog: React.FC<NewPaymentDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { toast } = useToast();
  const [apartments, setApartments] = useState<Apartment[]>([]);
  const [selectedApartmentId, setSelectedApartmentId] = useState<string>('');
  const [summary, setSummary] = useState<ApartmentPaymentSummary | null>(null);
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [notes, setNotes] = useState('');
  const [isLoadingApartments, setIsLoadingApartments] = useState(false);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Load apartments on open
  useEffect(() => {
    if (isOpen) {
      loadApartments();
    }
  }, [isOpen]);

  // Load summary when apartment is selected
  useEffect(() => {
    if (selectedApartmentId && selectedApartmentId !== 'placeholder') {
      loadSummary(parseInt(selectedApartmentId));
    } else {
      setSummary(null);
      setAmount('');
    }
  }, [selectedApartmentId]);

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

  const loadSummary = async (apartmentId: number) => {
    try {
      setIsLoadingSummary(true);
      setError('');
      const data = await paymentsApi.getApartmentSummary(apartmentId);
      setSummary(data);
      // Pre-fill amount with owed balance if negative (they owe money)
      if (data.balance < 0) {
        setAmount(Math.abs(data.balance).toFixed(2));
      } else {
        setAmount('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Грешка при зареждане на информацията');
      setSummary(null);
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApartmentId || selectedApartmentId === 'placeholder' || !amount) return;

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Моля въведете валидна сума');
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');
      
      // Get current month for the payment
      const now = new Date();
      const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
      
      await paymentsApi.create({
        apartment_id: parseInt(selectedApartmentId),
        amount: parsedAmount,
        month: currentMonth,
        payment_method: paymentMethod,
        notes: notes || undefined,
      });
      
      toast({
        title: '✅ Плащането е записано',
        description: `Ап. ${summary?.apartment_number} - ${parsedAmount.toFixed(2)} лв`,
        variant: 'success',
      });
      onSuccess();
      handleClose();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Грешка при запис на плащането';
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
    setSummary(null);
    setAmount('');
    setPaymentMethod('cash');
    setNotes('');
    setError('');
    onClose();
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('bg-BG');
  };

  const formatMonth = (month: string): string => {
    const [year, m] = month.split('-');
    const months = [
      'Яну', 'Фев', 'Мар', 'Апр', 'Май', 'Юни',
      'Юли', 'Авг', 'Сеп', 'Окт', 'Ное', 'Дек'
    ];
    return `${months[parseInt(m) - 1]} ${year}`;
  };

  const paymentMethods = [
    { value: 'cash', label: '💵 В брой' },
    { value: 'bank', label: '🏦 Банка' },
    { value: 'card', label: '💳 Карта' },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>💵 Ново плащане</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Apartment selector */}
          <div className="space-y-2">
            <Label>Изберете апартамент:</Label>
            <Select
              value={selectedApartmentId}
              onValueChange={setSelectedApartmentId}
              disabled={isLoadingApartments}
            >
              <SelectTrigger>
                <SelectValue placeholder="-- Изберете апартамент --" />
              </SelectTrigger>
              <SelectContent>
                {apartments.map((apt) => (
                  <SelectItem key={apt.id} value={apt.id.toString()}>
                    Ап. {apt.number} - {apt.owner_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Loading summary */}
          {isLoadingSummary && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          )}

          {/* Summary */}
          {summary && !isLoadingSummary && (
            <div className="space-y-4">
              {/* Account info */}
              <div className="bg-muted rounded-lg p-4">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-muted-foreground">Апартамент:</div>
                  <div className="font-medium">{summary.apartment_number}</div>
                  <div className="text-muted-foreground">Собственик:</div>
                  <div className="font-medium">{summary.owner_name}</div>
                  <div className="text-muted-foreground">Общо задължения:</div>
                  <div className="font-medium">{summary.total_obligations.toFixed(2)} лв</div>
                  <div className="text-muted-foreground">Общо плащания:</div>
                  <div className="font-medium">{summary.total_payments.toFixed(2)} лв</div>
                  <div className="text-muted-foreground">Баланс:</div>
                  <div className={cn(
                    "font-bold",
                    summary.balance < 0 && "text-destructive",
                    summary.balance > 0 && "text-blue-600",
                    summary.balance === 0 && "text-green-600"
                  )}>
                    {summary.balance < 0
                      ? `Дължи ${Math.abs(summary.balance).toFixed(2)} лв`
                      : summary.balance > 0
                        ? `Авансово ${summary.balance.toFixed(2)} лв`
                        : 'Изплатен'}
                  </div>
                </div>
              </div>

              {/* Recent payments */}
              {summary.recent_payments && summary.recent_payments.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-muted-foreground">Последни плащания:</Label>
                  <div className="space-y-1">
                    {summary.recent_payments.map((payment: RecentPayment) => (
                      <div
                        key={payment.id}
                        className="flex justify-between text-sm bg-muted/50 rounded px-3 py-1"
                      >
                        <span className="text-muted-foreground">
                          {formatDate(payment.payment_date)} - {formatMonth(payment.month)}
                        </span>
                        <span className="font-medium">{payment.amount.toFixed(2)} лв</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Quick fill button */}
              {summary.balance < 0 && (
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setAmount(Math.abs(summary.balance).toFixed(2))}
                  >
                    Въведи дължимата сума ({Math.abs(summary.balance).toFixed(2)} лв)
                  </Button>
                </div>
              )}

              {/* Amount input */}
              <div className="space-y-2">
                <Label htmlFor="amount">Сума (лв):</Label>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="text-2xl font-bold text-center h-14"
                  placeholder="0.00"
                  required
                />
              </div>

              {/* Payment method */}
              <div className="space-y-2">
                <Label>Начин на плащане:</Label>
                <div className="flex gap-2">
                  {paymentMethods.map((method) => (
                    <Button
                      key={method.value}
                      type="button"
                      variant="outline"
                      className={cn(
                        "flex-1",
                        paymentMethod === method.value &&
                          "border-primary bg-primary/10 text-primary"
                      )}
                      onClick={() => setPaymentMethod(method.value)}
                    >
                      {method.label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <Label htmlFor="notes">Бележки (незадължително):</Label>
                <Input
                  id="notes"
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Напр. платено от съпруга"
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Отказ
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || !summary || !amount || parseFloat(amount) <= 0}
              className="bg-green-600 hover:bg-green-700"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Записва се...
                </>
              ) : (
                '✅ Запиши плащане'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default NewPaymentDialog;