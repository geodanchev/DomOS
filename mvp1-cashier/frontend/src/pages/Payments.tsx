import React, { useState, useEffect } from 'react';
import { paymentsApi, apartmentsApi, receiptsApi } from '../services/api';
import type { Payment, Apartment } from '../types';
import NewPaymentDialog from '../components/NewPaymentDialog';
import { PermissionGate } from '../components/PermissionGate';
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

  const formatMonth = (month: string): string => {
    const [year, m] = month.split('-');
    const months = [
      'Яну', 'Фев', 'Мар', 'Апр', 'Май', 'Юни',
      'Юли', 'Авг', 'Сеп', 'Окт', 'Ное', 'Дек'
    ];
    return `${months[parseInt(m) - 1]} ${year}`;
  };

  const totalAmount = payments.reduce((sum, p) => sum + p.amount, 0);

  const handleDownloadReceipt = async (receiptId: number) => {
    try {
      await receiptsApi.downloadPdf(receiptId);
    } catch (err) {
      console.error('Error downloading receipt:', err);
      setError('Грешка при изтегляне на разписката');
    }
  };

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
      {/* Title */}
      <h2 className="text-2xl font-bold">💰 История на плащанията</h2>

      {/* Buttons */}
      <div className="flex gap-2 flex-wrap">
        <PermissionGate feature="payments" action="create">
          <Button
            onClick={() => setIsPaymentDialogOpen(true)}
            className="bg-green-600 hover:bg-green-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            <span className="hidden sm:inline">Ново плащане</span>
            <span className="sm:hidden">Ново</span>
          </Button>
        </PermissionGate>
        <Button variant="secondary" onClick={loadData}>
          <RefreshCw className="mr-2 h-4 w-4" />
          <span className="hidden sm:inline">Опресни</span>
        </Button>
      </div>

      {/* New Payment Dialog */}
      <NewPaymentDialog
        isOpen={isPaymentDialogOpen}
        onClose={() => setIsPaymentDialogOpen(false)}
        onSuccess={loadData}
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-green-500/10 rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Общо плащания</div>
          <div className="text-2xl font-bold text-green-600">{payments.length}</div>
        </div>
        <div className="bg-blue-500/10 rounded-lg p-4">
          <div className="text-sm text-muted-foreground">Обща сума</div>
          <div className="text-2xl font-bold text-blue-600">{totalAmount.toFixed(2)} лв</div>
        </div>
      </div>

      {/* Filters - Collapsible on mobile */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-end">
            <div className="flex-1 space-y-2">
              <Label>Апартамент:</Label>
              <Select
                value={filterApartment}
                onValueChange={setFilterApartment}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Всички" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Всички</SelectItem>
                  {apartments.map((apt) => (
                    <SelectItem key={apt.id} value={String(apt.id)}>
                      Ап. {apt.number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex-1 space-y-2">
              <Label>Месец:</Label>
              <Select
                value={filterMonth}
                onValueChange={setFilterMonth}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Всички" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Всички</SelectItem>
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
              className="w-full sm:w-auto"
            >
              <X className="mr-2 h-4 w-4" />
              Изчисти
            </Button>
          </div>
        </CardContent>
      </Card>

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
        /* Payments Table - Mobile Optimized */
        <Card>
          <CardHeader>
            <CardTitle>Плащания ({payments.length})</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">Ап.</TableHead>
                  <TableHead>Собственик</TableHead>
                  <TableHead className="text-right">Сума</TableHead>
                  <TableHead className="text-center w-20">Разписка</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {payments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-12 text-muted-foreground">
                      Няма намерени плащания
                    </TableCell>
                  </TableRow>
                ) : (
                  payments.map((payment) => (
                    <TableRow key={payment.id}>
                      <TableCell className="font-medium">
                        {payment.apartment_number}
                      </TableCell>
                      <TableCell className="max-w-[120px] truncate">
                        {payment.owner_name}
                      </TableCell>
                      <TableCell className="text-right font-medium text-green-600">
                        {payment.amount.toFixed(2)} лв
                      </TableCell>
                      <TableCell className="text-center">
                        {payment.receipt_id ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownloadReceipt(payment.receipt_id!)}
                            className="h-8 px-2"
                          >
                            📄
                          </Button>
                        ) : (
                          <span className="text-muted-foreground text-xs">-</span>
                        )}
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
