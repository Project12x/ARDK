import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { InventoryPage } from './pages/InventoryPage';
import { SettingsPage } from './pages/SettingsPage';
import { ProjectListPage } from './pages/ProjectListPage';
import { ProjectDetail } from './pages/ProjectDetail';
import { ProjectFlowPage } from './pages/ProjectFlowPage';
import { PortfolioPage } from './pages/PortfolioPage';
import { ProjectSchedule } from './pages/ProjectSchedule';
import { InboxPage } from './pages/InboxPage';
import { PurchaseQueuePage } from './pages/PurchaseQueuePage';
import { HelpPage } from './pages/HelpPage';
import { AssetRegistry } from './pages/AssetRegistry';
import { AssetDetail } from './pages/AssetDetail';
import { InstructionsPage } from './pages/InstructionsPage';
import { InstructionDetailPage } from './pages/InstructionDetailPage';
import { GoalsPage } from './pages/GoalsPage';
import { BlueprintPage } from './pages/BlueprintPage';
import { RoutinesPage } from './pages/RoutinesPage';
import { GalaxyPage } from './pages/GalaxyPage';
import SongsPage from './pages/SongsPage';
import SongDetailPage from './pages/SongDetailPage';
import AlbumDetailPage from './pages/AlbumDetailPage';
import GoalDetailPage from './pages/GoalDetailPage';
import { ComponentSandbox } from './pages/ComponentSandbox';
import { LayoutSandbox } from './pages/LayoutSandbox';
import RegistryTestPage from './pages/RegistryTestPage';
import { UniversalDataViewer } from './components/universal/UniversalDataViewer';
import { LibraryPage } from './pages/LibraryPage';
import { UniversalDetailPage } from './pages/UniversalDetailPage';
import { UniversalPageTest } from './pages/UniversalPageTest';
import { UniversalDetailSandbox } from './pages/UniversalDetailSandbox';

import { useEffect } from 'react';
import { validateSchemaRegistry } from './lib/schema-validator';

const queryClient = new QueryClient();

import { ErrorBoundary } from 'react-error-boundary';
import { UniversalErrorFallback } from './components/universal/UniversalErrorFallback';

// ...

function App() {
  useEffect(() => {
    // Run schema validation on boot to ensure backups are comprehensive
    validateSchemaRegistry();
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary FallbackComponent={UniversalErrorFallback} onReset={() => window.location.reload()}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="inbox" element={<InboxPage />} />
              <Route path="goals" element={<GoalsPage />} />
              <Route path="goals/:id" element={<GoalDetailPage />} />
              <Route path="projects" element={<ProjectListPage />} />
              <Route path="projects/:id" element={<ProjectDetail />} />
              <Route path="flow" element={<ProjectFlowPage />} />
              <Route path="portfolio" element={<PortfolioPage />} />
              <Route path="schedule" element={<ProjectSchedule />} />
              <Route path="inventory" element={<InventoryPage />} />
              <Route path="assets" element={<AssetRegistry />} />
              <Route path="assets/:id" element={<AssetDetail />} />
              <Route path="purchases" element={<PurchaseQueuePage />} />
              <Route path="instructions" element={<InstructionsPage />} />
              <Route path="instructions/:id" element={<InstructionDetailPage />} />
              <Route path="blueprints" element={<BlueprintPage />} />
              <Route path="routines" element={<RoutinesPage />} />
              <Route path="galaxy" element={<GalaxyPage />} />
              <Route path="songs" element={<SongsPage />} />
              <Route path="songs/:id" element={<SongDetailPage />} />
              <Route path="albums/:id" element={<AlbumDetailPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="library" element={<LibraryPage />} />
              <Route path="help" element={<HelpPage />} />


              {/* Developer Sandbox Routes */}
              <Route path="sandbox/components" element={<ComponentSandbox />} />
              <Route path="sandbox/layout" element={<LayoutSandbox />} />
              <Route path="sandbox/registry" element={<RegistryTestPage />} />
              <Route path="sandbox/universal-page" element={<UniversalPageTest />} />
              <Route path="sandbox/universal-detail" element={<UniversalDetailSandbox />} />
              <Route path="collection/:tableName" element={<UniversalDataViewer />} />
              <Route path="entity/:type/:id" element={<UniversalDetailPage />} />
            </Route>
          </Routes>
          <Toaster theme="dark" position="bottom-right" />
        </BrowserRouter>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

export default App;
