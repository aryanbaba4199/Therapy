import React, { useState } from "react";
import { Box } from "@mui/material";
import { FiStar } from "react-icons/fi";

interface RatingInputProps {
  value: number;
  onChange: (val: number) => void;
  max?: number;
  size?: number;
  disabled?: boolean;
}

export const RatingInput: React.FC<RatingInputProps> = ({
  value,
  onChange,
  max = 5,
  size = 28,
  disabled = false,
}) => {
  const [hoverValue, setHoverValue] = useState<number | null>(null);

  const displayValue = hoverValue !== null ? hoverValue : value;

  return (
    <Box
      className="flex items-center gap-1"
      role="radiogroup"
      aria-label="Rating"
    >
      {Array.from({ length: max }, (_, index) => {
        const starValue = index + 1;
        const isFilled = starValue <= displayValue;

        return (
          <button
            key={starValue}
            type="button"
            disabled={disabled}
            onClick={() => onChange(starValue)}
            onMouseEnter={() => !disabled && setHoverValue(starValue)}
            onMouseLeave={() => !disabled && setHoverValue(null)}
            className={`p-1 transition-transform focus:outline-none focus:scale-110 ${
              disabled ? "cursor-default" : "cursor-pointer hover:scale-110"
            }`}
            aria-label={`${starValue} of ${max} stars`}
            role="radio"
            aria-checked={value === starValue}
          >
            <FiStar
              size={size}
              className={`transition-colors ${
                isFilled
                  ? "fill-amber-400 text-amber-400"
                  : "text-neutral-300 hover:text-amber-200"
              }`}
            />
          </button>
        );
      })}
    </Box>
  );
};
