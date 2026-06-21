import React, { useState } from 'react';
import { paymentsApi } from '../services/api';
import type { ApartmentStatus } from '../types';
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
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface PaymentModalProps {
  apartment: ApartmentStatus;
  currentMonth: string;
  onClose: () => void;
  onSuccess: () => void;
}

const PaymentModal: React.FC<PaymentModalProps> = ({
  apartment,
  currentMonth,
  onClose,
  onSuccess,
}) => {
  const { toast } = useToast();
  
  // Balance is negative when they owe money, so we take the absolute value
  const amountOwed = apartment.balance < 0 ? Math.abs(apartment.balance) : 0;
  
  const [amount, setAmount] = useState(amountOwed > 0 ? amountOwed.toFixed(2) : '');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await paymentsApi.create({
        apartment_id: apartment.apartment_id,
        amount: parseFloat(amount),
        month: currentMonth,
        payment_method: paymentMethod,
        notes: notes || undefined,
      });
      toast({
        title: '✅ Плащането е записано',
        description: `Ап. ${apartment.apartment_number} - ${parseFloat(amount).toFixed(2)} лв`,
        variant: 'success',
      });
      onSuccess();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Грешка при запис на плащането';
      setError(errorMessage);
      toast({
        title: '❌ Грешка',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const quickAmounts = amountOwed > 0 
    ? [
        { label: 'Цяла сума', value: amountOwed },
        { label: '10 лв', value: 10 },
        { label: '20 лв', value: 20 },
        { label: '50 лв', value: 50 },
      ]
    : [
        { label: '10 лв', value: 10 },
        { label: '20 лв', value: 20 },
        { label: '50 лв', value: 50 },
        { label: '100 лв', value: 100 },
      ];

  const paymentMethods = [
    { value: 'cash', label: '💵 В брой' },
    { value: 'bank', label: '🏦 Банка' },
    { value: 'card', label: '💳 Карта' },
  ];

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>💵 Ново плащане</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Apartment info */}
          <div className="bg-muted rounded-lg p-4">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-muted-foreground">Апартамент:</div>
              <div className="font-medium">{apartment.apartment_number}</div>
              <div className="text-muted-foreground">Собственик:</div>
              <div className="font-medium">{apartment.owner_name}</div>
              <div className="text-muted-foreground">Общо задължения:</div>
              <div className="font-medium">{apartment.total_obligations.toFixed(2)} лв</div>
              <div className="text-muted-foreground">Общо плащания:</div>
              <div className="font-medium">{apartment.total_payments.toFixed(2)} лв</div>
              <div className="text-muted-foreground">Баланс:</div>
              <div className={cn(
                "font-bold",
                apartment.balance < 0 ? "text-red-600" : apartment.balance > 0 ? "text-blue-600" : "text-green-600"
              )}>
                {apartment.balance.toFixed(2)} лв
                {apartment.balance < 0 && " (дължи)"}
                {apartment.balance > 0 && " (авансово)"}
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Quick amounts */}
          <div className="space-y-2">
            <Label>Бързи суми:</Label>
            <div className="flex gap-2 flex-wrap">
              {quickAmounts.map((qa) => (
                <Button
                  key={qa.label}
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setAmount(qa.value.toFixed(2))}
                >
                  {qa.label}
                </Button>
              ))}
            </div>
          </div>

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
              required
              autoFocus
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

          {/* Actions */}
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isLoading}
            >
              Отказ
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !amount || parseFloat(amount) <= 0}
              className="bg-green-600 hover:bg-green-700"
            >
              {isLoading ? (
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

export default PaymentModal;
