import React, { useState } from 'react';
import { Box, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import DrawingCanvas from './DrawingCanvas';

interface Position {
  x: number;
  y: number;
}

interface DraggableDrawingCanvasProps {
  onClose: () => void;
  width?: number;
  height?: number;
}

const DraggableDrawingCanvas: React.FC<DraggableDrawingCanvasProps> = ({ 
  onClose,
  width = 300,
  height = 200
}) => {
  const [position, setPosition] = useState<Position>({ x: window.innerWidth / 2 - width / 2, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState<Position>({ x: 0, y: 0 });

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    setIsDragging(true);
    setDragOffset({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;

    const newX = e.clientX - dragOffset.x;
    const newY = e.clientY - dragOffset.y;

    // Ensure the canvas stays within the viewport
    const maxX = window.innerWidth - width - 20; // 20px padding from edges
    const maxY = window.innerHeight - height - 20;

    setPosition({
      x: Math.max(20, Math.min(newX, maxX)),
      y: Math.max(20, Math.min(newY, maxY))
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        zIndex: 1000,
        bgcolor: 'background.paper',
        borderRadius: 2,
        boxShadow: 3,
        cursor: isDragging ? 'grabbing' : 'auto',
        userSelect: 'none'
      }}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Header with drag handle and close button */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          p: 0.5,
          borderBottom: '1px solid',
          borderColor: 'divider',
          cursor: 'grab'
        }}
        onMouseDown={handleMouseDown}
      >
        <DragIndicatorIcon sx={{ color: 'text.secondary' }} />
        <IconButton 
          size="small" 
          onClick={onClose}
          sx={{ 
            '&:hover': {
              bgcolor: 'error.light',
              color: 'white'
            }
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Drawing canvas */}
      <Box sx={{ p: 1 }}>
        <DrawingCanvas width={width} height={height} />
      </Box>
    </Box>
  );
};

export default DraggableDrawingCanvas;
