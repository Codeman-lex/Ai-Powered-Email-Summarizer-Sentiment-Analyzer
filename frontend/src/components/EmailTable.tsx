import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  IconButton,
  Chip,
  Box,
  Typography,
  Tooltip,
  TablePagination,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Avatar,
  Divider
} from '@mui/material';
import { 
  MoreVert as MoreVertIcon,
  Delete as DeleteIcon,
  Archive as ArchiveIcon,
  MoveToInbox as MoveToInboxIcon,
  LocalOffer as TagIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  AttachFile as AttachFileIcon,
  Label as LabelIcon,
  ArrowUpward as UpIcon,
  ArrowDownward as DownIcon,
  LowPriority as LowPriorityIcon
} from '@mui/icons-material';
import { formatDistance } from 'date-fns';

// Types
import { Email } from '../types/email';

// Interfaces
interface EmailTableProps {
  emails: Email[];
  totalCount: number;
  onSelectionChange?: (selectedIds: string[]) => void;
  onDelete?: (ids: string[]) => void;
  onArchive?: (ids: string[]) => void;
  onMove?: (ids: string[], destination: string) => void;
  onStar?: (id: string, starred: boolean) => void;
}

const EmailTable: React.FC<EmailTableProps> = ({
  emails,
  totalCount,
  onSelectionChange,
  onDelete,
  onArchive,
  onMove,
  onStar
}) => {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  const [currentEmail, setCurrentEmail] = useState<string | null>(null);
  
  // Handle row selection
  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = emails.map((email) => email.id);
      setSelected(newSelected);
      if (onSelectionChange) onSelectionChange(newSelected);
      return;
    }
    setSelected([]);
    if (onSelectionChange) onSelectionChange([]);
  };

  const handleRowClick = (event: React.MouseEvent<unknown>, id: string) => {
    // Prevent navigation if clicking on a control
    if ((event.target as HTMLElement).closest('button, a, .MuiCheckbox-root')) {
      return;
    }
    
    navigate(`/emails/${id}`);
  };

  const handleCheckboxClick = (event: React.MouseEvent<unknown>, id: string) => {
    event.stopPropagation();
    const selectedIndex = selected.indexOf(id);
    let newSelected: string[] = [];

    if (selectedIndex === -1) {
      newSelected = [...selected, id];
    } else {
      newSelected = selected.filter((itemId) => itemId !== id);
    }

    setSelected(newSelected);
    if (onSelectionChange) onSelectionChange(newSelected);
  };

  const handleStarClick = (event: React.MouseEvent<unknown>, id: string, starred: boolean) => {
    event.stopPropagation();
    if (onStar) onStar(id, !starred);
  };

  // Pagination handlers
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Context menu handlers
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, emailId: string) => {
    event.stopPropagation();
    setMenuAnchorEl(event.currentTarget);
    setCurrentEmail(emailId);
  };

  const handleMenuClose = () => {
    setMenuAnchorEl(null);
    setCurrentEmail(null);
  };

  const handleDelete = () => {
    if (currentEmail && onDelete) {
      onDelete([currentEmail]);
    }
    handleMenuClose();
  };

  const handleArchive = () => {
    if (currentEmail && onArchive) {
      onArchive([currentEmail]);
    }
    handleMenuClose();
  };

  // Helper functions
  const isSelected = (id: string) => selected.indexOf(id) !== -1;

  const getSenderInitials = (senderName: string) => {
    const parts = senderName.split(' ');
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive': return '#4caf50';
      case 'negative': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getImportanceColor = (score: number) => {
    if (score >= 0.7) return '#f44336';
    if (score >= 0.4) return '#ff9800';
    return undefined;
  };

  return (
    <>
      <TableContainer component={Paper} elevation={0}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selected.length > 0 && selected.length < emails.length}
                  checked={emails.length > 0 && selected.length === emails.length}
                  onChange={handleSelectAllClick}
                  inputProps={{ 'aria-label': 'select all emails' }}
                />
              </TableCell>
              <TableCell width="50px"></TableCell>
              <TableCell>Sender / Subject</TableCell>
              <TableCell>Summary</TableCell>
              <TableCell align="center" width="100px">Sentiment</TableCell>
              <TableCell align="right" width="100px">Date</TableCell>
              <TableCell width="50px"></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {emails.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    No emails found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              emails
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((email) => {
                  const isItemSelected = isSelected(email.id);
                  
                  return (
                    <TableRow
                      hover
                      onClick={(event) => handleRowClick(event, email.id)}
                      role="checkbox"
                      aria-checked={isItemSelected}
                      tabIndex={-1}
                      key={email.id}
                      selected={isItemSelected}
                      sx={{ 
                        cursor: 'pointer',
                        backgroundColor: email.unread ? 'rgba(25, 118, 210, 0.04)' : 'inherit'
                      }}
                    >
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={isItemSelected}
                          onClick={(event) => handleCheckboxClick(event, email.id)}
                        />
                      </TableCell>
                      <TableCell padding="none">
                        <IconButton
                          size="small"
                          onClick={(event) => handleStarClick(event, email.id, email.starred)}
                        >
                          {email.starred ? (
                            <StarIcon fontSize="small" color="warning" />
                          ) : (
                            <StarBorderIcon fontSize="small" />
                          )}
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar 
                            sx={{ 
                              width: 36, 
                              height: 36, 
                              mr: 2,
                              bgcolor: email.importance_score >= 0.7 ? 'error.main' : 
                                email.importance_score >= 0.4 ? 'warning.main' : 'primary.main'
                            }}
                          >
                            {getSenderInitials(email.sender_name)}
                          </Avatar>
                          <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                              <Typography
                                variant="subtitle2"
                                sx={{ 
                                  fontWeight: email.unread ? 700 : 400,
                                  mr: 1
                                }}
                              >
                                {email.sender_name}
                              </Typography>
                              {email.has_attachments && (
                                <Tooltip title="Has attachments">
                                  <AttachFileIcon fontSize="small" color="action" sx={{ ml: 1, opacity: 0.7 }} />
                                </Tooltip>
                              )}
                              {email.importance_score >= 0.4 && (
                                <Tooltip title={`Priority: ${Math.round(email.importance_score * 100)}%`}>
                                  <LowPriorityIcon 
                                    fontSize="small" 
                                    sx={{ ml: 1, color: getImportanceColor(email.importance_score) }} 
                                  />
                                </Tooltip>
                              )}
                            </Box>
                            <Typography
                              variant="body2"
                              noWrap
                              sx={{ 
                                maxWidth: '300px',
                                fontWeight: email.unread ? 600 : 400
                              }}
                            >
                              {email.subject}
                            </Typography>
                            {email.categories && email.categories.length > 0 && (
                              <Box sx={{ mt: 0.5, display: 'flex', flexWrap: 'wrap' }}>
                                {email.categories.slice(0, 2).map((category) => (
                                  <Chip
                                    key={category}
                                    label={category}
                                    size="small"
                                    variant="outlined"
                                    sx={{ mr: 0.5, mb: 0.5 }}
                                  />
                                ))}
                                {email.categories.length > 2 && (
                                  <Chip
                                    label={`+${email.categories.length - 2}`}
                                    size="small"
                                    sx={{ mr: 0.5, mb: 0.5 }}
                                  />
                                )}
                              </Box>
                            )}
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          noWrap
                          sx={{ 
                            maxWidth: '400px',
                            fontWeight: email.unread ? 600 : 400
                          }}
                        >
                          {email.summary}
                        </Typography>
                        {email.action_items && email.action_items.length > 0 && (
                          <Box sx={{ mt: 0.5 }}>
                            <Chip
                              icon={<TagIcon fontSize="small" />}
                              label={`${email.action_items.length} action item${email.action_items.length > 1 ? 's' : ''}`}
                              size="small"
                              color="info"
                              sx={{ mr: 0.5 }}
                            />
                          </Box>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={email.sentiment}
                          size="small"
                          sx={{
                            bgcolor: getSentimentColor(email.sentiment),
                            color: 'white'
                          }}
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="caption" color="text.secondary">
                          {formatDistance(new Date(email.date), new Date(), { addSuffix: true })}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={(event) => handleMenuOpen(event, email.id)}
                        >
                          <MoreVertIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
      
      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchorEl}
        open={Boolean(menuAnchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleArchive}>
          <ListItemIcon>
            <ArchiveIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Archive</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDelete}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <MoveToInboxIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Move to...</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <ListItemIcon>
            <LabelIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Apply Label</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
};

export default EmailTable; 