import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Box, Grid, Typography, Paper, CircularProgress, useTheme, Divider } from '@mui/material';
import { BarChart, Bar, PieChart, Pie, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell, Legend } from 'recharts';
import { format } from 'date-fns';

// Components
import PageHeader from '../components/PageHeader';
import StatCard from '../components/StatCard';
import EmailTable from '../components/EmailTable';
import FilterBar from '../components/FilterBar';
import CategoryChips from '../components/CategoryChips';

// Services
import { getEmailAnalytics, getEmails } from '../services/emailService';

// Types
import { EmailAnalytics, Email, EmailFilter } from '../types/email';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const [filters, setFilters] = useState<EmailFilter>({
    category: 'all',
    timeRange: 'week',
    sort: 'date',
    sentiment: 'all',
  });

  // Analytics data query
  const { 
    data: analyticsData, 
    isLoading: isLoadingAnalytics 
  } = useQuery<EmailAnalytics>(['analytics', filters.timeRange], () => 
    getEmailAnalytics(filters.timeRange)
  );

  // Emails data query
  const {
    data: emailsData,
    isLoading: isLoadingEmails
  } = useQuery(['emails', filters], () => 
    getEmails(filters)
  );

  // Colors for charts
  const sentimentColors = {
    positive: theme.palette.success.main,
    neutral: theme.palette.grey[500],
    negative: theme.palette.error.main,
  };
  
  const categoryColors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.info.main,
    theme.palette.warning.main,
    theme.palette.error.main,
    '#8884d8',
    '#82ca9d',
    '#ffc658',
  ];

  // Filter handlers
  const handleFilterChange = (newFilters: Partial<EmailFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  if (isLoadingAnalytics) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="80vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader 
        title="Email Intelligence Dashboard" 
        subtitle={`Data for ${format(new Date(), 'MMMM d, yyyy')}`} 
      />

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <FilterBar 
          filters={filters} 
          onFilterChange={handleFilterChange} 
        />
      </Paper>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Emails Processed"
            value={analyticsData?.totalEmails || 0}
            icon="email"
            trend={analyticsData?.emailTrend || 0}
            trendLabel={`vs last ${filters.timeRange}`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Average Sentiment"
            value={analyticsData?.averageSentimentScore ? `${(analyticsData.averageSentimentScore * 100).toFixed(1)}%` : '0%'}
            icon="sentiment"
            color={analyticsData?.dominantSentiment ? sentimentColors[analyticsData.dominantSentiment as keyof typeof sentimentColors] : 'primary'}
            trend={analyticsData?.sentimentTrend || 0}
            trendLabel="Sentiment trend"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Response Rate"
            value={analyticsData?.responseRate ? `${(analyticsData.responseRate * 100).toFixed(1)}%` : '0%'}
            icon="rate"
            trend={analyticsData?.responseRateTrend || 0}
            trendLabel="Response rate trend"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="High Priority"
            value={analyticsData?.highPriorityCount || 0}
            icon="priority"
            color="error"
            trend={analyticsData?.priorityTrend || 0}
            trendLabel="Priority emails trend"
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Email Volume & Sentiment</Typography>
            <Box height={300}>
              {analyticsData?.volumeByDay ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analyticsData.volumeByDay}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="positive" name="Positive" fill={sentimentColors.positive} stackId="a" />
                    <Bar dataKey="neutral" name="Neutral" fill={sentimentColors.neutral} stackId="a" />
                    <Bar dataKey="negative" name="Negative" fill={sentimentColors.negative} stackId="a" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box display="flex" height="100%" alignItems="center" justifyContent="center">
                  <Typography color="text.secondary">No data available</Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Email Categories</Typography>
            <Box height={300} display="flex" flexDirection="column" justifyContent="center">
              {analyticsData?.categoriesDistribution && analyticsData.categoriesDistribution.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={analyticsData.categoriesDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      fill="#8884d8"
                      paddingAngle={2}
                      dataKey="value"
                      nameKey="name"
                      label
                    >
                      {analyticsData.categoriesDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={categoryColors[index % categoryColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Box display="flex" height="100%" alignItems="center" justifyContent="center">
                  <Typography color="text.secondary">No data available</Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Category Chips */}
      {analyticsData?.topCategories && (
        <Box sx={{ mb: 3 }}>
          <CategoryChips 
            categories={analyticsData.topCategories}
            onCategoryClick={(category) => handleFilterChange({ category })}
            selectedCategory={filters.category}
          />
        </Box>
      )}

      {/* Email List */}
      <Paper sx={{ p: 0, mb: 3, overflow: 'hidden' }}>
        <Typography variant="h6" sx={{ p: 2, pb: 0 }}>Recent Emails</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ px: 2, pb: 2 }}>
          Showing emails with applied filters
        </Typography>
        <Divider />
        {isLoadingEmails ? (
          <Box display="flex" justifyContent="center" alignItems="center" p={4}>
            <CircularProgress />
          </Box>
        ) : (
          <EmailTable 
            emails={emailsData?.emails || []} 
            totalCount={emailsData?.pagination.total || 0}
          />
        )}
      </Paper>
    </Box>
  );
};

export default Dashboard; 