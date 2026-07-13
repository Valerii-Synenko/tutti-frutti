// Package storage holds an in-memory stock store for the demo inventory-service.
// A production version of this would sit on Postgres or Redis; in-memory is
// intentional here to keep the service dependency-free and fast to reset in tests.
package storage

import "sync"

type Item struct {
	SKU               string
	QuantityAvailable int32
	UnitPriceEUR      float64
}

type Store struct {
	mu    sync.RWMutex
	items map[string]*Item
}

func NewStore() *Store {
	s := &Store{items: make(map[string]*Item)}
	s.seed()
	return s
}

// seed mirrors the fruit slugs used in catalogue-service's seed data so the
// two services agree on identifiers in the demo environment.
func (s *Store) seed() {
	seedData := []*Item{
		{SKU: "pink-lady-apple", QuantityAvailable: 240, UnitPriceEUR: 0.65},
		{SKU: "alphonso-mango", QuantityAvailable: 60, UnitPriceEUR: 3.40},
		{SKU: "wild-blueberries", QuantityAvailable: 35, UnitPriceEUR: 4.80},
		{SKU: "dragon-fruit", QuantityAvailable: 50, UnitPriceEUR: 3.10},
		{SKU: "croatian-fig", QuantityAvailable: 20, UnitPriceEUR: 5.20},
		{SKU: "cavendish-banana", QuantityAvailable: 500, UnitPriceEUR: 0.39},
		{SKU: "kherson-watermelon", QuantityAvailable: 120, UnitPriceEUR: 1.95},
	}
	for _, item := range seedData {
		s.items[item.SKU] = item
	}
}

func (s *Store) Get(sku string) (*Item, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	item, ok := s.items[sku]
	return item, ok
}

func (s *Store) BatchGet(skus []string) []*Item {
	s.mu.RLock()
	defer s.mu.RUnlock()
	result := make([]*Item, 0, len(skus))
	for _, sku := range skus {
		if item, ok := s.items[sku]; ok {
			result = append(result, item)
		}
	}
	return result
}

// Reserve decrements available quantity for an order. Returns the remaining
// quantity and whether the reservation succeeded.
func (s *Store) Reserve(sku string, quantity int32) (int32, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()

	item, ok := s.items[sku]
	if !ok || item.QuantityAvailable < quantity {
		if ok {
			return item.QuantityAvailable, false
		}
		return 0, false
	}
	item.QuantityAvailable -= quantity
	return item.QuantityAvailable, true
}
