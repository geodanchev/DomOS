import React, { useState, useEffect } from 'react';
import { paymentsApi, apartmentsApi } from '../services/api';
import type { Payment, Apartment } from '../types';
import NewPaymentDialog from '../components/NewPaymentDialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { RefreshCw, Plus, X, Loader2 } from 'lucide-react';

const Payments: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [apartments, setApartments] = useState<Apartment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [filterApartment, setFilterApartment] = useState<string>('');
  const [filterMonth, setFilterMonth] = useState<string>('');
  
  // New payment dialog
  const [isPaymentDialogOpen, setIsPaymentDialogOpen] = useState(false);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [paymentsData, apartmentsData] = await Promise.all([
        paymentsApi.getAll(
          filterApartment ? parseInt(filterApartment) : undefined,
          filterMonth || undefined
        ),
        apartmentsApi.getAll(),
      ]);
      setPayments(paymentsData.items);
      setApartments(apartmentsData.items);
      setError('');
    } catch (err) {
      setError('Грешка при зареждане на плащанията');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterApartment, filterMonth]);

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

  const getPaymentMethodLabel = (method: string): string => {
    switch (method) {
      case 'cash': return '💵 В брой';
      case 'bank': return '🏦 Банка';
      case 'card': return '💳 Карта';
      default: return method;
    }
  };

  const totalAmount = payments.reduce((sum, p) => sum + p.amount, 0);

  // Generate month options (last 12 months)
  const getMonthOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
      options.push({ value, label: formatMonth(value) });
    }
    return options;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">💰 История на плащанията</h2>
        <div className="flex gap-2">
          <Button
            onClick={() => setIsPaymentDialogOpen(true)}
            className="bg-green-600 hover:bg-green-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            Ново плащане
          </Button>
          <Button variant="secondary" onClick={loadData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Опресни
          </Button>
        </div>
      </div>

      {/* New Payment Dialog */}
      <NewPaymentDialog
        isOpen={isPaymentDialogOpen}
        onClose={() => setIsPaymentDialogOpen(false)}
        onSuccess={loadData}
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="flex-1 min-w-[200px] space-y-2">
              <Label>Апартамент:</Label>
              <Select
                value={filterApartment}
                onValueChange={setFilterApartment}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Всички апартаменти" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Всички апартаменти</SelectItem>
                  {apartments.map((apt) => (
                    <SelectItem key={apt.id} value={String(apt.id)}>
                      Ап. {apt.number} - {apt.owner_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex-1 min-w-[200px] space-y-2">
              <Label>Месец:</Label>
              <Select
                value={filterMonth}
                onValueChange={setFilterMonth}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Всички месеци" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Всички месеци</SelectItem>
                  {getMonthOptions().map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              variant="secondary"
              onClick={() => {
                setFilterApartment('');
                setFilterMonth('');
              }}
            >
              <X className="mr-2 h-4 w-4" />
              Изчисти филтри
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary */}
      <div className="bg-primary/10 border border-primary/20 rounded-lg px-6 py-4">
        <div className="flex justify-between items-center">
          <span className="text-primary">
            Показани: <strong>{payments.length}</strong> плащания
          </span>
          <span className="text-primary">
            Обща сума: <strong>{totalAmount.toFixed(2)} лв</strong>
          </span>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-6 py-4 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </div>
      ) : (
        /* Payments Table */
        <Card>
          <CardHeader>
            <CardTitle>Плащания</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Дата</TableHead>
                  <TableHead>Ап.</TableHead>
                  <TableHead>Собственик</TableHead>
                  <TableHead>За месец</TableHead>
                  <TableHead className="text-right">Сума</TableHead>
                  <TableHead>Начин</TableHead>
                  <TableHead>Приел</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {payments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-12 text-muted-foreground">
                      Няма намерени плащания
                    </TableCell>
                  </TableRow>
                ) : (
                  payments.map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell>
                        {formatDate(payment.payment_date)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {payment.apartment_number}
                      </TableCell>
                      <TableCell>
                        {payment.owner_name}
                      </TableCell>
                      <TableCell>
                        {formatMonth(payment.month)}
                      </TableCell>
                      <TableCell className="text-right font-medium text-green-600">
                        {payment.amount.toFixed(2)} лв
                      </TableCell>
                      <TableCell>
                        {getPaymentMethodLabel(payment.payment_method)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {payment.collected_by_name || '-'}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Payments;
