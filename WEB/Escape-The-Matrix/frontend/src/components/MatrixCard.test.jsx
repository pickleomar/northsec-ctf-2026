import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import MatrixCard from './MatrixCard';

// Mocking fetch
global.fetch = vi.fn();

// Mocking createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mock-gif-url');

function createFetchResponse(ok, status, headers, blob) {
    return {
        ok,
        status,
        headers: new Headers(headers),
        blob: () => Promise.resolve(blob),
    };
}

describe('MatrixCard', () => {
    beforeEach(() => {
        fetch.mockClear();
        global.URL.createObjectURL.mockClear();
    });

    it('renders initial state correctly', () => {
        render(<MatrixCard />);
        expect(screen.getByText('Escape Matrix')).toBeInTheDocument();
    });

    it('clicking button fetches GIF and updates DOM id', async () => {
        const fragment = btoa('frag1');
        const response = createFetchResponse(true, 200, { 'X-Matrix-Id': fragment }, new Blob(['gif-data']));
        fetch.mockResolvedValue(response);

        render(<MatrixCard />);
        
        const button = screen.getByText('Escape Matrix');
        const card = screen.getByTestId('matrix-card-div');
        const initialId = card.id;

        fireEvent.click(button);

        await waitFor(() => {
            expect(fetch).toHaveBeenCalledTimes(1);
        });

        await waitFor(() => {
            const urlSafeFragment = fragment.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
            expect(card.id).toBe(`${initialId}.${urlSafeFragment}`);
            expect(screen.getByAltText('Matrix GIF')).toHaveAttribute('src', 'mock-gif-url');
        });
    });

    it('handles "Gone" response from server', async () => {
        const response = createFetchResponse(false, 410, {}, new Blob());
        fetch.mockResolvedValue(response);

        render(<MatrixCard />);
        fireEvent.click(screen.getByText('Escape Matrix'));

        await waitFor(() => {
            expect(screen.getByText(/Congratulations.*escaped the Matrix/i)).toBeInTheDocument();
        });
    });
});
