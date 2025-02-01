import React, { useRef, useEffect, useState } from 'react';
import { 
  Box, 
  IconButton, 
  Tooltip, 
  ToggleButtonGroup, 
  ToggleButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import CreateIcon from '@mui/icons-material/Create';
import TimelineIcon from '@mui/icons-material/Timeline';
import CropSquareIcon from '@mui/icons-material/CropSquare';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import StarIcon from '@mui/icons-material/Star';
import FavoriteIcon from '@mui/icons-material/Favorite';
import FormatSizeIcon from '@mui/icons-material/FormatSize';

interface DrawingCanvasProps {
  width?: number;
  height?: number;
}

type DrawingTool = 'pencil' | 'line' | 'rectangle' | 'circle' | 'star' | 'heart' | 'text';

const colors = ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF'];

export const DrawingCanvas: React.FC<DrawingCanvasProps> = ({ 
  width = 300, 
  height = 300 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentColor, setCurrentColor] = useState('#000000');
  const [currentTool, setCurrentTool] = useState<DrawingTool>('pencil');
  const [textDialogOpen, setTextDialogOpen] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [textPosition, setTextPosition] = useState<{ x: number; y: number } | null>(null);
  const [lastImageData, setLastImageData] = useState<ImageData | null>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);
  const startPointRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const context = canvas.getContext('2d');
    if (!context) return;

    context.scale(dpr, dpr);
    context.lineCap = 'round';
    context.lineJoin = 'round';
    context.lineWidth = 3;
    contextRef.current = context;
  }, [width, height]);

  const getCoordinates = (event: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    const x = ('touches' in event)
      ? event.touches[0].clientX - rect.left
      : event.clientX - rect.left;
    const y = ('touches' in event)
      ? event.touches[0].clientY - rect.top
      : event.clientY - rect.top;

    return { x, y };
  };

  const handleToolChange = (_event: React.MouseEvent<HTMLElement>, tool: DrawingTool | null) => {
    if (tool) {
      setCurrentTool(tool);
      if (tool === 'text') {
        // Don't open dialog immediately, wait for click on canvas
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.style.cursor = 'text';
        }
      } else {
        const canvas = canvasRef.current;
        if (canvas) {
          canvas.style.cursor = 'crosshair';
        }
      }
    }
  };

  const startDrawing = (event: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    const { x, y } = getCoordinates(event);
    
    if (currentTool === 'text') {
      setTextPosition({ x, y });
      setTextDialogOpen(true);
      return;
    }

    const context = contextRef.current;
    const canvas = canvasRef.current;
    if (!context || !canvas) return;

    // Save the current canvas state before starting to draw
    if (currentTool !== 'pencil') {
      const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      setLastImageData(imageData);
    }

    setIsDrawing(true);
    startPointRef.current = { x, y };

    if (currentTool === 'pencil') {
      context.beginPath();
      context.moveTo(x, y);
    }
  };

  const draw = (event: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !contextRef.current) return;
    event.preventDefault();
    const { x, y } = getCoordinates(event);
    const context = contextRef.current;
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    if (currentTool === 'pencil') {
      context.lineTo(x, y);
      context.stroke();
    } else {
      // For shapes, restore the last state and draw preview
      if (lastImageData) {
        context.putImageData(lastImageData, 0, 0);
      }
      
      // Draw preview shape
      drawShape(context, startPointRef.current.x, startPointRef.current.y, x, y);
    }
  };

  const stopDrawing = () => {
    if (!isDrawing || !contextRef.current) return;
    
    const context = contextRef.current;
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (currentTool === 'pencil') {
      context.closePath();
    } else {
      // For shapes, save the final state
      const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      setLastImageData(imageData);
    }
    
    setIsDrawing(false);
  };

  const drawShape = (
    context: CanvasRenderingContext2D,
    startX: number,
    startY: number,
    endX: number,
    endY: number
  ) => {
    context.beginPath();
    context.strokeStyle = currentColor;
    context.fillStyle = currentColor;

    switch (currentTool) {
      case 'line':
        context.moveTo(startX, startY);
        context.lineTo(endX, endY);
        break;
      case 'rectangle':
        const rectX = Math.min(startX, endX);
        const rectY = Math.min(startY, endY);
        const width = Math.abs(endX - startX);
        const height = Math.abs(endY - startY);
        context.rect(rectX, rectY, width, height);
        break;
      case 'circle':
        const radius = Math.sqrt(
          Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2)
        );
        context.arc(startX, startY, radius, 0, 2 * Math.PI);
        break;
      case 'star':
        const spikes = 5;
        const outerRadius = Math.sqrt(
          Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2)
        );
        const innerRadius = outerRadius * 0.4;

        for (let i = 0; i < spikes * 2; i++) {
          const radius = i % 2 === 0 ? outerRadius : innerRadius;
          const angle = (i * Math.PI) / spikes - Math.PI / 2;
          const x = startX + Math.cos(angle) * radius;
          const y = startY + Math.sin(angle) * radius;
          if (i === 0) context.moveTo(x, y);
          else context.lineTo(x, y);
        }
        context.closePath();
        break;
      case 'heart':
        const size = Math.max(
          Math.abs(endX - startX),
          Math.abs(endY - startY)
        );
        
        // Start at the bottom point
        context.moveTo(startX, startY + size * 0.75);
        
        // Left curve
        context.bezierCurveTo(
          startX - size * 0.4, startY + size * 0.35,  // control point 1
          startX - size * 0.4, startY - size * 0.15,  // control point 2
          startX, startY                              // end point
        );
        
        // Right curve
        context.bezierCurveTo(
          startX + size * 0.4, startY - size * 0.15,  // control point 1
          startX + size * 0.4, startY + size * 0.35,  // control point 2
          startX, startY + size * 0.75                // end point
        );
        break;
      case 'text':
        context.font = '20px Arial';
        context.fillText(textInput || 'ABC', endX, endY);
        context.stroke(); // Add stroke for text
        return; // Return early for text since it only needs fill and stroke
    }

    context.stroke();
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const context = contextRef.current;
    if (!canvas || !context) return;
    context.clearRect(0, 0, canvas.width, canvas.height);
    setLastImageData(null);
  };

  const handleTextSubmit = () => {
    if (!textInput || !textPosition || !contextRef.current) return;
    
    const context = contextRef.current;
    context.font = '20px Arial';
    context.fillStyle = currentColor;
    context.fillText(textInput, textPosition.x, textPosition.y);
    
    setTextDialogOpen(false);
    setTextInput('');
    setTextPosition(null);
  };

  return (
    <Box sx={{ 
      position: 'relative',
      backgroundColor: '#ffffff',
      borderRadius: 2,
      boxShadow: 1,
      p: 1
    }}>
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        gap: 1,
        mb: 1
      }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
          <ToggleButtonGroup
            size="small"
            value={currentTool}
            exclusive
            onChange={handleToolChange}
            aria-label="drawing tool"
          >
            <ToggleButton value="pencil" aria-label="pencil">
              <Tooltip title="Pencil">
                <CreateIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="line" aria-label="line">
              <Tooltip title="Line">
                <TimelineIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="rectangle" aria-label="rectangle">
              <Tooltip title="Rectangle">
                <CropSquareIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="circle" aria-label="circle">
              <Tooltip title="Circle">
                <RadioButtonUncheckedIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
          </ToggleButtonGroup>

          <Tooltip title="Clear canvas">
            <IconButton onClick={clearCanvas} size="small">
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 1 }}>
          <ToggleButtonGroup
            size="small"
            value={currentTool}
            exclusive
            onChange={handleToolChange}
            aria-label="more shapes"
          >
            <ToggleButton value="star" aria-label="star">
              <Tooltip title="Star">
                <StarIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="heart" aria-label="heart">
              <Tooltip title="Heart">
                <FavoriteIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="text" aria-label="text">
              <Tooltip title="Text">
                <FormatSizeIcon fontSize="small" />
              </Tooltip>
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {colors.map((color) => (
            <Tooltip key={color} title="Select color">
              <Box
                onClick={() => setCurrentColor(color)}
                sx={{
                  width: 24,
                  height: 24,
                  backgroundColor: color,
                  borderRadius: '50%',
                  cursor: 'pointer',
                  border: currentColor === color ? '2px solid #000' : '1px solid #ccc'
                }}
              />
            </Tooltip>
          ))}
        </Box>
      </Box>

      <canvas
        ref={canvasRef}
        onMouseDown={startDrawing}
        onMouseMove={draw}
        onMouseUp={stopDrawing}
        onMouseLeave={stopDrawing}
        onTouchStart={startDrawing}
        onTouchMove={draw}
        onTouchEnd={stopDrawing}
        style={{
          border: '1px solid #ccc',
          borderRadius: '8px',
          touchAction: 'none'
        }}
      />

      {/* Text Input Dialog */}
      <Dialog 
        open={textDialogOpen} 
        onClose={() => setTextDialogOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Enter Text</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Your text"
            fullWidth
            variant="outlined"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleTextSubmit();
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTextDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleTextSubmit} variant="contained" color="primary">
            Add Text
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DrawingCanvas;
