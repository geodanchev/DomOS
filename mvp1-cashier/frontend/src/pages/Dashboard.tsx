import React, { useState, useEffect } from 'react';
import { dashboardApi } from '../services/api';
import type { CashierDashboard, FundBalance, ApartmentStatus } from '../types';
import PaymentModal from '../components/PaymentModal';
import NewObligationDialog from '../components/NewObligationDialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { RefreshCw, Loader2, Plus } from 'lucide-react';

const Dashboard: React.FC = () => {
  const [dashboard, setDashboard] = useState<CashierDashboard | null>(null);
  const [fund, setFund] = useState<FundBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedApartment, setSelectedApartment] = useState<ApartmentStatus | null>(null);
  const [isObligationDialogOpen, setIsObligationDialogOpen] = useState(false);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [dashboardData, fundData] = await Promise.all([
        dashboardApi.getDashboard(),
        dashboardApi.getFundBalance(),
      ]);
      setDashboard(dashboardData);
      setFund(fundData);
      setError('');
    } catch (err) {
      setError('Грешка при зареждане на данните');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePaymentSuccess = () => {
    setSelectedApartment(null);
    loadData();
  };

  const formatMonth = (month: string): string => {
    const [year, m] = month.split('-');
    const months = [
      'Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни',
      'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'
    ];
    return `${months[parseInt(m) - 1]} ${year}`;
  };

  const getStatusBadge = (status: string, statusDisplay: string) => {
    switch (status) {
      case 'paid':
        return <Badge variant="success">✓ {statusDisplay}</Badge>;
      case 'credit':
        return <Badge variant="default" className="bg-blue-500">💰 {statusDisplay}</Badge>;
      case 'owes':
      default:
        return <Badge variant="destructive">✗ {statusDisplay}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-destructive/10 border border-destructive/20 text-destructive px-6 py-4 rounded-lg">
        {error}
        <Button variant="link" onClick={loadData} className="ml-4">
          Опитай пак
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">
          📊 Табло - {dashboard && formatMonth(dashboard.current_month)}
        </h2>
        <div className="flex gap-2">
          <Button
            onClick={() => setIsObligationDialogOpen(true)}
            className="bg-amber-600 hover:bg-amber-700"
          >
            <Plus className="mr-2 h-4 w-4" />
            Ново задължение
          </Button>
          <Button variant="secondary" onClick={loadData}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Опресни
          </Button>
        </div>
      </div>

      {/* New Obligation Dialog */}
      <NewObligationDialog
        isOpen={isObligationDialogOpen}
        onClose={() => setIsObligationDialogOpen(false)}
        onSuccess={loadData}
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Fund Balance */}
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium opacity-90">💰 Баланс на фонда</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{fund?.current_balance.toFixed(2)} лв</div>
          </CardContent>
        </Card>

        {/* Collected total */}
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium opacity-90">📥 Общо събрани</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboard?.total_collected.toFixed(2)} лв</div>
          </CardContent>
        </Card>

        {/* Total Owed */}
        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium opacity-90">⏳ Общо дължимо</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboard?.total_owed.toFixed(2)} лв</div>
          </CardContent>
        </Card>

        {/* Collection Rate */}
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium opacity-90">📈 Събираемост</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboard?.collection_rate}%</div>
            <div className="text-sm opacity-90 mt-1">
              {dashboard?.paid_count} изплатени / {dashboard?.total_apartments} общо
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="flex gap-4 flex-wrap">
        <Badge variant="success" className="px-4 py-2 text-sm">
          ✓ Изплатени: {dashboard?.paid_count}
        </Badge>
        <Badge variant="destructive" className="px-4 py-2 text-sm">
          ✗ Дължат: {dashboard?.owes_count}
        </Badge>
      </div>

      {/* Apartments Table */}
      <Card>
        <CardHeader>
          <CardTitle>🏠 Апартаменти</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Ап.</TableHead>
                <TableHead>Собственик</TableHead>
                <TableHead className="text-right">Задължения</TableHead>
                <TableHead className="text-right">Плащания</TableHead>
                <TableHead className="text-right">Баланс</TableHead>
                <TableHead className="text-center">Статус</TableHead>
                <TableHead className="text-center">Действие</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dashboard?.apartments.map((apt) => (
                <TableRow key={apt.apartment_id}>
                  <TableCell className="font-medium">
                    {apt.apartment_number}
                  </TableCell>
                  <TableCell>{apt.owner_name}</TableCell>
                  <TableCell className="text-right">
                    {apt.total_obligations.toFixed(2)} лв
                  </TableCell>
                  <TableCell className="text-right">
                    {apt.total_payments.toFixed(2)} лв
                  </TableCell>
                  <TableCell className={`text-right font-medium ${apt.balance < 0 ? 'text-red-600' : apt.balance > 0 ? 'text-blue-600' : 'text-green-600'}`}>
                    {apt.balance.toFixed(2)} лв
                  </TableCell>
                  <TableCell className="text-center">
                    {getStatusBadge(apt.status, apt.status_display)}
                  </TableCell>
                  <TableCell className="text-center">
                    {apt.status === 'owes' && (
                      <Button
                        size="sm"
                        onClick={() => setSelectedApartment(apt)}
                      >
                        💵 Плащане
                      </Button>
                    )}
                    {apt.status === 'paid' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedApartment(apt)}
                      >
                        💵 Авансово
                      </Button>
                    )}
                    {apt.status === 'credit' && (
                      <span className="text-sm text-muted-foreground">Авансово</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Payment Modal */}
      {selectedApartment && (
        <PaymentModal
          apartment={selectedApartment}
          currentMonth={dashboard?.current_month || ''}
          onClose={() => setSelectedApartment(null)}
          onSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
};

export default Dashboard;
