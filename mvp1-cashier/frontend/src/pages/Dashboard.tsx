import React, { useState, useEffect } from 'react';
import { dashboardApi } from '../services/api';
import type { CashierDashboard, FundBalance, ApartmentStatus } from '../types';
import PaymentModal from '../components/PaymentModal';
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
import { RefreshCw, Loader2 } from 'lucide-react';

const Dashboard: React.FC = () => {
  const [dashboard, setDashboard] = useState<CashierDashboard | null>(null);
  const [fund, setFund] = useState<FundBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedApartment, setSelectedApartment] = useState<ApartmentStatus | null>(null);

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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'paid':
        return <Badge variant="success">✓ Платено</Badge>;
      case 'partial':
        return <Badge variant="warning">◐ Частично</Badge>;
      default:
        return <Badge variant="destructive">✗ Неплатено</Badge>;
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
        <Button variant="secondary" onClick={loadData}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Опресни
        </Button>
      </div>

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

        {/* Collected this month */}
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium opacity-90">📥 Събрано този месец</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboard?.total_collected.toFixed(2)} лв</div>
          </CardContent>
        </Card>

        {/* Remaining */}
        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium opacity-90">⏳ Остават за събиране</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dashboard?.total_unpaid.toFixed(2)} лв</div>
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
              {dashboard?.paid_count} платили / {dashboard?.total_apartments} общо
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <div className="flex gap-4 flex-wrap">
        <Badge variant="success" className="px-4 py-2 text-sm">
          ✓ Платили: {dashboard?.paid_count}
        </Badge>
        <Badge variant="warning" className="px-4 py-2 text-sm">
          ◐ Частично: {dashboard?.partial_count}
        </Badge>
        <Badge variant="destructive" className="px-4 py-2 text-sm">
          ✗ Неплатили: {dashboard?.unpaid_count}
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
                <TableHead className="text-right">Дължи</TableHead>
                <TableHead className="text-right">Платил</TableHead>
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
                    {apt.amount_due.toFixed(2)} лв
                  </TableCell>
                  <TableCell className="text-right">
                    {apt.amount_paid.toFixed(2)} лв
                  </TableCell>
                  <TableCell className="text-center">
                    {getStatusBadge(apt.status)}
                  </TableCell>
                  <TableCell className="text-center">
                    {apt.status !== 'paid' && (
                      <Button
                        size="sm"
                        onClick={() => setSelectedApartment(apt)}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        💵 Плати
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Payment Modal */}
      {selectedApartment && dashboard && (
        <PaymentModal
          apartment={selectedApartment}
          month={dashboard.current_month}
          onClose={() => setSelectedApartment(null)}
          onSuccess={handlePaymentSuccess}
        />
      )}
    </div>
  );
};

export default Dashboard;
